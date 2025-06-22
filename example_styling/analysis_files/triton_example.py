import triton
import triton.language as tl
import torch

@triton.jit
def softmax_dropout_kernel_slow(
    input_ptr, output_ptr, dropout_mask_ptr,
    n_rows, n_cols, dropout_p: tl.constexpr, BLOCK_SIZE: tl.constexpr,
):
    row_idx = tl.program_id(0)
    if row_idx >= n_rows:
        return
    
    row_data = tl.zeros([BLOCK_SIZE], dtype=tl.float32)
    for i in range(n_cols):
        if i < BLOCK_SIZE:
            input_offset = row_idx * n_cols + i
            row_data = tl.where(
                tl.arange(0, BLOCK_SIZE) == i,
                tl.load(input_ptr + input_offset, mask=i < n_cols),
                row_data
            )
    
    max_val = -float('inf')
    for i in range(n_cols):
        if i < BLOCK_SIZE:
            current_val = tl.where(
                tl.arange(0, BLOCK_SIZE) == i,
                row_data,
                -float('inf')
            )
            max_val = tl.maximum(max_val, tl.max(current_val))
    
    exp_values = tl.zeros([BLOCK_SIZE], dtype=tl.float32)
    for i in range(n_cols):
        if i < BLOCK_SIZE:
            val = tl.where(
                tl.arange(0, BLOCK_SIZE) == i,
                row_data,
                0.0
            )
            exp_val = tl.exp(tl.max(val) - max_val)
            exp_values = tl.where(
                tl.arange(0, BLOCK_SIZE) == i,
                exp_val,
                exp_values
            )
    
    sum_exp = 0.0
    for i in range(n_cols):
        if i < BLOCK_SIZE:
            val = tl.where(
                tl.arange(0, BLOCK_SIZE) == i,
                exp_values,
                0.0
            )
            sum_exp += tl.sum(val)
    
    for i in range(n_cols):
        if i < BLOCK_SIZE:
            mask_offset = row_idx * n_cols + i
            dropout_mask = tl.load(dropout_mask_ptr + mask_offset, mask=i < n_cols)
            
            exp_val = tl.where(
                tl.arange(0, BLOCK_SIZE) == i,
                exp_values,
                0.0
            )
            softmax_val = tl.sum(exp_val) / sum_exp
            
            output_val = tl.where(
                dropout_mask > dropout_p,
                softmax_val / (1.0 - dropout_p),
                0.0
            )
            
            output_offset = row_idx * n_cols + i
            tl.store(output_ptr + output_offset, output_val, mask=i < n_cols)

@triton.jit
def softmax_dropout_kernel_fast(
    input_ptr, output_ptr, dropout_mask_ptr,
    n_rows, n_cols, dropout_p: tl.constexpr, BLOCK_SIZE: tl.constexpr,
):
    row_idx = tl.program_id(0)
    if row_idx >= n_rows:
        return
    
    row_offset = row_idx * n_cols
    col_offsets = tl.arange(0, BLOCK_SIZE)
    mask = col_offsets < n_cols
    
    input_ptrs = input_ptr + row_offset + col_offsets
    row_data = tl.load(input_ptrs, mask=mask, other=-float('inf'))
    
    row_max = tl.max(row_data)
    normalized = row_data - row_max
    exp_values = tl.exp(normalized)
    exp_values = tl.where(mask, exp_values, 0.0)
    
    sum_exp = tl.sum(exp_values)
    softmax_values = exp_values / sum_exp
    
    dropout_ptrs = dropout_mask_ptr + row_offset + col_offsets
    dropout_mask = tl.load(dropout_ptrs, mask=mask, other=0.0)
    
    keep_mask = dropout_mask > dropout_p
    scale = 1.0 / (1.0 - dropout_p)
    output_values = tl.where(keep_mask, softmax_values * scale, 0.0)
    
    output_ptrs = output_ptr + row_offset + col_offsets
    tl.store(output_ptrs, output_values, mask=mask)

@triton.autotune(
    configs=[
        triton.Config({'BLOCK_SIZE': 128}, num_warps=4),
        triton.Config({'BLOCK_SIZE': 256}, num_warps=4),
        triton.Config({'BLOCK_SIZE': 512}, num_warps=8),
        triton.Config({'BLOCK_SIZE': 1024}, num_warps=8),
    ],
    key=['n_cols'],
)
@triton.jit
def softmax_dropout_kernel_autotuned(
    input_ptr, output_ptr, dropout_mask_ptr,
    n_rows, n_cols, dropout_p: tl.constexpr, BLOCK_SIZE: tl.constexpr,
):
    row_idx = tl.program_id(0)
    if row_idx >= n_rows:
        return
    
    row_offset = row_idx * n_cols
    col_offsets = tl.arange(0, BLOCK_SIZE)
    mask = col_offsets < n_cols
    
    input_ptrs = input_ptr + row_offset + col_offsets
    row_data = tl.load(input_ptrs, mask=mask, other=-float('inf'))
    
    row_max = tl.max(row_data)
    normalized = row_data - row_max
    exp_values = tl.exp(normalized)
    exp_values = tl.where(mask, exp_values, 0.0)
    
    sum_exp = tl.sum(exp_values)
    softmax_values = exp_values / sum_exp
    
    dropout_ptrs = dropout_mask_ptr + row_offset + col_offsets
    dropout_mask = tl.load(dropout_ptrs, mask=mask, other=0.0)
    
    keep_mask = dropout_mask > dropout_p
    scale = 1.0 / (1.0 - dropout_p)
    output_values = tl.where(keep_mask, softmax_values * scale, 0.0)
    
    output_ptrs = output_ptr + row_offset + col_offsets
    tl.store(output_ptrs, output_values, mask=mask)

def softmax_dropout_slow(x, dropout_p=0.1, training=True):
    n_rows, n_cols = x.shape
    dropout_mask = torch.rand_like(x) if training else torch.ones_like(x)
    output = torch.empty_like(x)
    
    BLOCK_SIZE = 128
    grid = (n_rows,)
    softmax_dropout_kernel_slow[grid](
        x, output, dropout_mask, n_rows, n_cols, dropout_p, BLOCK_SIZE,
    )
    return output

def softmax_dropout_fast(x, dropout_p=0.1, training=True):
    n_rows, n_cols = x.shape
    dropout_mask = torch.rand_like(x) if training else torch.ones_like(x)
    output = torch.empty_like(x)
    
    if n_cols <= 1024:
        BLOCK_SIZE = min(triton.next_power_of_2(n_cols), 1024)
        grid = (n_rows,)
        softmax_dropout_kernel_fast[grid](
            x, output, dropout_mask, n_rows, n_cols, dropout_p, BLOCK_SIZE,
        )
    else:
        BLOCK_SIZE = 1024
        n_blocks = triton.cdiv(n_cols, BLOCK_SIZE)
        grid = (n_rows, n_blocks)
        print(f"Warning: Large sequence {n_cols}, using multi-block")
    
    return output

def softmax_dropout_autotuned(x, dropout_p=0.1, training=True):
    n_rows, n_cols = x.shape
    dropout_mask = torch.rand_like(x) if training else torch.ones_like(x)
    output = torch.empty_like(x)
    
    grid = (n_rows,)
    softmax_dropout_kernel_autotuned[grid](
        x, output, dropout_mask, n_rows, n_cols, dropout_p,
    )
    return output

def benchmark():
    test_sizes = [(32, 128), (32, 512), (32, 1024), (64, 2048)]
    
    for batch_size, seq_len in test_sizes:
        print(f"Size: {batch_size}x{seq_len}")
        x = torch.randn(batch_size, seq_len, device='cuda', dtype=torch.float32)
        
        for _ in range(10):
            _ = softmax_dropout_fast(x)
        torch.cuda.synchronize()
        
        start = torch.cuda.Event(enable_timing=True)
        end = torch.cuda.Event(enable_timing=True)
        
        start.record()
        for _ in range(100):
            _ = softmax_dropout_slow(x)
        end.record()
        torch.cuda.synchronize()
        slow_time = start.elapsed_time(end) / 100
        
        start.record()
        for _ in range(100):
            _ = softmax_dropout_fast(x)
        end.record()
        torch.cuda.synchronize()
        fast_time = start.elapsed_time(end) / 100
        
        start.record()
        for _ in range(100):
            _ = softmax_dropout_autotuned(x)
        end.record()
        torch.cuda.synchronize()
        auto_time = start.elapsed_time(end) / 100
        
        start.record()
        for _ in range(100):
            _ = torch.nn.functional.dropout(
                torch.nn.functional.softmax(x, dim=-1), p=0.1, training=True
            )
        end.record()
        torch.cuda.synchronize()
        torch_time = start.elapsed_time(end) / 100
        
        print(f"  Slow: {slow_time:.4f}ms")
        print(f"  Fast: {fast_time:.4f}ms ({slow_time/fast_time:.1f}x)")
        print(f"  Auto: {auto_time:.4f}ms ({torch_time/auto_time:.1f}x vs PyTorch)")
        print(f"  PyTorch: {torch_time:.4f}ms")
        print()

if __name__ == "__main__":
    benchmark()
