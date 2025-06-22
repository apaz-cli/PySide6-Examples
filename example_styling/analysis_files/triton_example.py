import triton
import triton.language as tl
import torch
import numpy as np

@triton.jit
def softmax_dropout_kernel(
    input_ptr, output_ptr, dropout_mask_ptr,
    n_rows, n_cols,
    dropout_p: tl.constexpr,
    BLOCK_SIZE: tl.constexpr,
):
    """
    Fused softmax + dropout kernel with several performance issues:
    1. Suboptimal memory access patterns
    2. Inefficient block sizing
    3. Redundant computations
    4. Missing vectorization opportunities
    5. Poor register usage
    """
    
    # Get current row
    row_idx = tl.program_id(0)
    
    if row_idx >= n_rows:
        return
    
    # Load input row one element at a time (INEFFICIENT!)
    row_data = tl.zeros([BLOCK_SIZE], dtype=tl.float32)
    for i in range(n_cols):
        if i < BLOCK_SIZE:
            input_offset = row_idx * n_cols + i
            row_data = tl.where(
                tl.arange(0, BLOCK_SIZE) == i,
                tl.load(input_ptr + input_offset, mask=i < n_cols),
                row_data
            )
    
    # Find max (inefficiently computed multiple times)
    max_val = tl.float32(-float('inf'))
    for i in range(n_cols):
        if i < BLOCK_SIZE:
            current_val = tl.where(
                tl.arange(0, BLOCK_SIZE) == i,
                row_data,
                tl.float32(-float('inf'))
            )
            # This is doing element-wise max incorrectly
            max_val = tl.maximum(max_val, tl.max(current_val))
    
    # Subtract max and compute exp (redundant loads)
    exp_values = tl.zeros([BLOCK_SIZE], dtype=tl.float32)
    for i in range(n_cols):
        if i < BLOCK_SIZE:
            val = tl.where(
                tl.arange(0, BLOCK_SIZE) == i,
                row_data,
                0.0
            )
            exp_val = tl.exp(tl.max(val) - max_val)  # Inefficient: should subtract max from val
            exp_values = tl.where(
                tl.arange(0, BLOCK_SIZE) == i,
                exp_val,
                exp_values
            )
    
    # Compute sum (another inefficient loop)
    sum_exp = 0.0
    for i in range(n_cols):
        if i < BLOCK_SIZE:
            val = tl.where(
                tl.arange(0, BLOCK_SIZE) == i,
                exp_values,
                0.0
            )
            sum_exp += tl.sum(val)
    
    # Apply softmax and dropout element by element (very inefficient!)
    for i in range(n_cols):
        if i < BLOCK_SIZE:
            # Load dropout mask
            mask_offset = row_idx * n_cols + i
            dropout_mask = tl.load(dropout_mask_ptr + mask_offset, mask=i < n_cols)
            
            # Get softmax value
            exp_val = tl.where(
                tl.arange(0, BLOCK_SIZE) == i,
                exp_values,
                0.0
            )
            softmax_val = tl.sum(exp_val) / sum_exp
            
            # Apply dropout
            output_val = tl.where(
                dropout_mask > dropout_p,
                softmax_val / (1.0 - dropout_p),  # Scale by keep probability
                0.0
            )
            
            # Store result
            output_offset = row_idx * n_cols + i
            tl.store(output_ptr + output_offset, output_val, mask=i < n_cols)


def softmax_dropout_triton(x, dropout_p=0.1, training=True):
    """
    Wrapper function for the inefficient softmax + dropout kernel
    """
    n_rows, n_cols = x.shape
    
    # Generate dropout mask
    if training:
        dropout_mask = torch.rand_like(x)
    else:
        dropout_mask = torch.ones_like(x)
    
    # Allocate output
    output = torch.empty_like(x)
    
    # Choose a suboptimal block size
    BLOCK_SIZE = 128  # Often too small for modern GPUs
    
    # Launch kernel
    grid = (n_rows,)
    softmax_dropout_kernel[grid](
        x, output, dropout_mask,
        n_rows, n_cols,
        dropout_p,
        BLOCK_SIZE,
    )
    
    return output


# Example usage and performance test
def test_kernel():
    # Create test data
    batch_size, seq_len = 32, 512
    x = torch.randn(batch_size, seq_len, device='cuda', dtype=torch.float32)
    
    # Test our inefficient kernel
    print("Testing inefficient Triton kernel...")
    torch.cuda.synchronize()
    start = torch.cuda.Event(enable_timing=True)
    end = torch.cuda.Event(enable_timing=True)
    
    start.record()
    for _ in range(100):
        result_triton = softmax_dropout_triton(x, dropout_p=0.1)
    end.record()
    torch.cuda.synchronize()
    triton_time = start.elapsed_time(end) / 100
    
    # Compare with PyTorch implementation
    print("Testing PyTorch reference...")
    start.record()
    for _ in range(100):
        result_torch = torch.nn.functional.dropout(
            torch.nn.functional.softmax(x, dim=-1), 
            p=0.1, 
            training=True
        )
    end.record()
    torch.cuda.synchronize()
    torch_time = start.elapsed_time(end) / 100
    
    print(f"Triton kernel time: {triton_time:.4f} ms")
    print(f"PyTorch time: {torch_time:.4f} ms")
    print(f"Speedup: {torch_time / triton_time:.2f}x")
    
    return result_triton, result_torch


if __name__ == "__main__":
    test_kernel()


"""
PERFORMANCE IMPROVEMENT OPPORTUNITIES:

1. **Memory Access Patterns**: 
   - Load entire rows at once using vectorized loads
   - Eliminate redundant loads in loops
   - Use coalesced memory access patterns

2. **Algorithmic Improvements**:
   - Compute max, exp, and sum in single passes
   - Use online algorithms for numerical stability
   - Fuse operations to reduce memory bandwidth

3. **Block Size Optimization**:
   - Use larger block sizes (256, 512, 1024)
   - Make block size adaptive based on problem size
   - Consider multiple blocks per row for large sequences

4. **Vectorization**:
   - Process multiple elements per thread
   - Use SIMD operations where possible
   - Optimize for GPU warp size (32 threads)

5. **Register Usage**:
   - Minimize temporary arrays
   - Reuse registers effectively
   - Reduce control flow divergence

6. **Numerical Stability**:
   - Use more stable softmax computation
   - Handle edge cases better
   - Consider mixed precision

Expected improvements: 5-20x speedup with proper optimization!
"""
