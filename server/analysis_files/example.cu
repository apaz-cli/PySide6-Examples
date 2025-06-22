#include <cuda_runtime.h>
#include <iostream>
#include <vector>
#include <chrono>

// CUDA kernel for vector addition
__global__ void vectorAdd(const float* a, const float* b, float* c, int n) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    
    if (idx < n) {
        c[idx] = a[idx] + b[idx];
    }
}

// CUDA kernel for matrix multiplication
__global__ void matrixMul(const float* a, const float* b, float* c, 
                         int m, int n, int k) {
    int row = blockIdx.y * blockDim.y + threadIdx.y;
    int col = blockIdx.x * blockDim.x + threadIdx.x;
    
    if (row < m && col < n) {
        float sum = 0.0f;
        for (int i = 0; i < k; ++i) {
            sum += a[row * k + i] * b[i * n + col];
        }
        c[row * n + col] = sum;
    }
}

// Shared memory optimized matrix multiplication
__global__ void matrixMulShared(const float* a, const float* b, float* c,
                               int m, int n, int k) {
    __shared__ float tile_a[16][16];
    __shared__ float tile_b[16][16];
    
    int row = blockIdx.y * blockDim.y + threadIdx.y;
    int col = blockIdx.x * blockDim.x + threadIdx.x;
    
    float sum = 0.0f;
    
    for (int tile = 0; tile < (k + 15) / 16; ++tile) {
        // Load tiles into shared memory
        if (row < m && tile * 16 + threadIdx.x < k) {
            tile_a[threadIdx.y][threadIdx.x] = a[row * k + tile * 16 + threadIdx.x];
        } else {
            tile_a[threadIdx.y][threadIdx.x] = 0.0f;
        }
        
        if (col < n && tile * 16 + threadIdx.y < k) {
            tile_b[threadIdx.y][threadIdx.x] = b[(tile * 16 + threadIdx.y) * n + col];
        } else {
            tile_b[threadIdx.y][threadIdx.x] = 0.0f;
        }
        
        __syncthreads();
        
        // Compute partial sum
        for (int i = 0; i < 16; ++i) {
            sum += tile_a[threadIdx.y][i] * tile_b[i][threadIdx.x];
        }
        
        __syncthreads();
    }
    
    if (row < m && col < n) {
        c[row * n + col] = sum;
    }
}

// Error checking macro
#define CUDA_CHECK(call) \
    do { \
        cudaError_t error = call; \
        if (error != cudaSuccess) { \
            std::cerr << "CUDA error at " << __FILE__ << ":" << __LINE__ \
                      << " - " << cudaGetErrorString(error) << std::endl; \
            exit(1); \
        } \
    } while(0)

int main() {
    const int n = 1024 * 1024;  // 1M elements
    const int size = n * sizeof(float);
    
    // Host vectors
    std::vector<float> h_a(n), h_b(n), h_c(n);
    
    // Initialize host vectors
    for (int i = 0; i < n; ++i) {
        h_a[i] = static_cast<float>(i);
        h_b[i] = static_cast<float>(i * 2);
    }
    
    // Device vectors
    float *d_a, *d_b, *d_c;
    CUDA_CHECK(cudaMalloc(&d_a, size));
    CUDA_CHECK(cudaMalloc(&d_b, size));
    CUDA_CHECK(cudaMalloc(&d_c, size));
    
    // Copy data to device
    CUDA_CHECK(cudaMemcpy(d_a, h_a.data(), size, cudaMemcpyHostToDevice));
    CUDA_CHECK(cudaMemcpy(d_b, h_b.data(), size, cudaMemcpyHostToDevice));
    
    // Launch configuration
    int blockSize = 256;
    int gridSize = (n + blockSize - 1) / blockSize;
    
    // Time the kernel execution
    auto start = std::chrono::high_resolution_clock::now();
    
    vectorAdd<<<gridSize, blockSize>>>(d_a, d_b, d_c, n);
    CUDA_CHECK(cudaDeviceSynchronize());
    
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
    
    // Copy result back to host
    CUDA_CHECK(cudaMemcpy(h_c.data(), d_c, size, cudaMemcpyDeviceToHost));
    
    // Verify result
    bool success = true;
    for (int i = 0; i < std::min(10, n); ++i) {
        float expected = h_a[i] + h_b[i];
        if (std::abs(h_c[i] - expected) > 1e-5) {
            success = false;
            break;
        }
    }
    
    std::cout << "Vector addition " << (success ? "PASSED" : "FAILED") << std::endl;
    std::cout << "Execution time: " << duration.count() << " microseconds" << std::endl;
    
    // Get device properties
    cudaDeviceProp prop;
    CUDA_CHECK(cudaGetDeviceProperties(&prop, 0));
    std::cout << "Device: " << prop.name << std::endl;
    std::cout << "Compute capability: " << prop.major << "." << prop.minor << std::endl;
    std::cout << "Max threads per block: " << prop.maxThreadsPerBlock << std::endl;
    std::cout << "Shared memory per block: " << prop.sharedMemPerBlock / 1024 << " KB" << std::endl;
    
    // Cleanup
    CUDA_CHECK(cudaFree(d_a));
    CUDA_CHECK(cudaFree(d_b));
    CUDA_CHECK(cudaFree(d_c));
    
    return 0;
}
