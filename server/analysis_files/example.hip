#include <hip/hip_runtime.h>
#include <iostream>
#include <vector>
#include <chrono>

// HIP kernel for parallel reduction
__global__ void reduce_sum(const float* input, float* output, int n) {
    __shared__ float sdata[256];
    
    int tid = threadIdx.x;
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    
    // Load data into shared memory
    sdata[tid] = (i < n) ? input[i] : 0.0f;
    __syncthreads();
    
    // Perform reduction in shared memory
    for (int s = blockDim.x / 2; s > 0; s >>= 1) {
        if (tid < s) {
            sdata[tid] += sdata[tid + s];
        }
        __syncthreads();
    }
    
    // Write result for this block to global memory
    if (tid == 0) {
        output[blockIdx.x] = sdata[0];
    }
}

// HIP kernel for SAXPY operation (y = a*x + y)
__global__ void saxpy(float a, const float* x, float* y, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    
    if (i < n) {
        y[i] = a * x[i] + y[i];
    }
}

// HIP kernel using wavefront intrinsics
__global__ void warp_reduce_sum(const float* input, float* output, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    float val = (i < n) ? input[i] : 0.0f;
    
    // Wavefront-level reduction using shuffle operations
    for (int offset = 32; offset > 0; offset /= 2) {
        val += __shfl_down(val, offset);
    }
    
    // First thread in each wavefront writes to global memory
    if ((threadIdx.x & 63) == 0) {  // AMD wavefront size is 64
        atomicAdd(output, val);
    }
}

// Error checking macro for HIP
#define HIP_CHECK(call) \
    do { \
        hipError_t error = call; \
        if (error != hipSuccess) { \
            std::cerr << "HIP error at " << __FILE__ << ":" << __LINE__ \
                      << " - " << hipGetErrorString(error) << std::endl; \
            exit(1); \
        } \
    } while(0)

void print_device_info() {
    int deviceCount;
    HIP_CHECK(hipGetDeviceCount(&deviceCount));
    
    for (int i = 0; i < deviceCount; ++i) {
        hipDeviceProp_t prop;
        HIP_CHECK(hipGetDeviceProperties(&prop, i));
        
        std::cout << "Device " << i << ": " << prop.name << std::endl;
        std::cout << "  Compute capability: " << prop.major << "." << prop.minor << std::endl;
        std::cout << "  Global memory: " << prop.totalGlobalMem / (1024*1024) << " MB" << std::endl;
        std::cout << "  Shared memory per block: " << prop.sharedMemPerBlock / 1024 << " KB" << std::endl;
        std::cout << "  Max threads per block: " << prop.maxThreadsPerBlock << std::endl;
        std::cout << "  Wavefront size: " << prop.warpSize << std::endl;
        std::cout << "  Multiprocessors: " << prop.multiProcessorCount << std::endl;
    }
}

int main() {
    print_device_info();
    
    const int n = 1024 * 1024;  // 1M elements
    const int size = n * sizeof(float);
    
    // Host vectors
    std::vector<float> h_x(n), h_y(n);
    
    // Initialize host vectors
    for (int i = 0; i < n; ++i) {
        h_x[i] = static_cast<float>(i % 100);
        h_y[i] = static_cast<float>(i % 50);
    }
    
    // Device vectors
    float *d_x, *d_y, *d_result;
    HIP_CHECK(hipMalloc(&d_x, size));
    HIP_CHECK(hipMalloc(&d_y, size));
    HIP_CHECK(hipMalloc(&d_result, sizeof(float)));
    
    // Copy data to device
    HIP_CHECK(hipMemcpy(d_x, h_x.data(), size, hipMemcpyHostToDevice));
    HIP_CHECK(hipMemcpy(d_y, h_y.data(), size, hipMemcpyHostToDevice));
    
    // SAXPY operation
    const float alpha = 2.0f;
    int blockSize = 256;
    int gridSize = (n + blockSize - 1) / blockSize;
    
    auto start = std::chrono::high_resolution_clock::now();
    
    hipLaunchKernelGGL(saxpy, gridSize, blockSize, 0, 0, alpha, d_x, d_y, n);
    HIP_CHECK(hipDeviceSynchronize());
    
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
    
    std::cout << "\nSAXPY execution time: " << duration.count() << " microseconds" << std::endl;
    
    // Reduction operation
    std::vector<float> h_temp(gridSize);
    float *d_temp;
    HIP_CHECK(hipMalloc(&d_temp, gridSize * sizeof(float)));
    
    start = std::chrono::high_resolution_clock::now();
    
    // First reduction pass
    hipLaunchKernelGGL(reduce_sum, gridSize, blockSize, 0, 0, d_y, d_temp, n);
    
    // Second reduction pass (if needed)
    if (gridSize > 1) {
        int finalGridSize = (gridSize + blockSize - 1) / blockSize;
        hipLaunchKernelGGL(reduce_sum, finalGridSize, blockSize, 0, 0, d_temp, d_result, gridSize);
    } else {
        HIP_CHECK(hipMemcpy(d_result, d_temp, sizeof(float), hipMemcpyDeviceToDevice));
    }
    
    HIP_CHECK(hipDeviceSynchronize());
    
    end = std::chrono::high_resolution_clock::now();
    duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
    
    // Copy result back and verify
    float gpu_sum;
    HIP_CHECK(hipMemcpy(&gpu_sum, d_result, sizeof(float), hipMemcpyDeviceToHost));
    
    // CPU verification
    HIP_CHECK(hipMemcpy(h_y.data(), d_y, size, hipMemcpyDeviceToHost));
    float cpu_sum = 0.0f;
    for (int i = 0; i < n; ++i) {
        cpu_sum += h_y[i];
    }
    
    std::cout << "Reduction execution time: " << duration.count() << " microseconds" << std::endl;
    std::cout << "GPU sum: " << gpu_sum << std::endl;
    std::cout << "CPU sum: " << cpu_sum << std::endl;
    std::cout << "Difference: " << std::abs(gpu_sum - cpu_sum) << std::endl;
    
    // Test wavefront reduction
    float zero = 0.0f;
    HIP_CHECK(hipMemcpy(d_result, &zero, sizeof(float), hipMemcpyHostToDevice));
    
    start = std::chrono::high_resolution_clock::now();
    
    hipLaunchKernelGGL(warp_reduce_sum, gridSize, blockSize, 0, 0, d_x, d_result, n);
    HIP_CHECK(hipDeviceSynchronize());
    
    end = std::chrono::high_resolution_clock::now();
    duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
    
    float warp_sum;
    HIP_CHECK(hipMemcpy(&warp_sum, d_result, sizeof(float), hipMemcpyDeviceToHost));
    
    float cpu_x_sum = 0.0f;
    for (int i = 0; i < n; ++i) {
        cpu_x_sum += h_x[i];
    }
    
    std::cout << "\nWavefront reduction execution time: " << duration.count() << " microseconds" << std::endl;
    std::cout << "GPU wavefront sum: " << warp_sum << std::endl;
    std::cout << "CPU sum: " << cpu_x_sum << std::endl;
    std::cout << "Difference: " << std::abs(warp_sum - cpu_x_sum) << std::endl;
    
    // Cleanup
    HIP_CHECK(hipFree(d_x));
    HIP_CHECK(hipFree(d_y));
    HIP_CHECK(hipFree(d_temp));
    HIP_CHECK(hipFree(d_result));
    
    return 0;
}
