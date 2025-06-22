use std::fmt;

// Rust example with ownership, borrowing, and error handling
#[derive(Debug, Clone)]
struct Vector3D {
    x: f64,
    y: f64,
    z: f64,
}

impl Vector3D {
    fn new(x: f64, y: f64, z: f64) -> Self {
        Vector3D { x, y, z }
    }
    
    fn magnitude(&self) -> f64 {
        (self.x * self.x + self.y * self.y + self.z * self.z).sqrt()
    }
    
    fn normalize(&self) -> Result<Vector3D, String> {
        let mag = self.magnitude();
        if mag == 0.0 {
            Err("Cannot normalize zero vector".to_string())
        } else {
            Ok(Vector3D {
                x: self.x / mag,
                y: self.y / mag,
                z: self.z / mag,
            })
        }
    }
    
    fn dot_product(&self, other: &Vector3D) -> f64 {
        self.x * other.x + self.y * other.y + self.z * other.z
    }
    
    fn cross_product(&self, other: &Vector3D) -> Vector3D {
        Vector3D {
            x: self.y * other.z - self.z * other.y,
            y: self.z * other.x - self.x * other.z,
            z: self.x * other.y - self.y * other.x,
        }
    }
}

impl fmt::Display for Vector3D {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "({:.2}, {:.2}, {:.2})", self.x, self.y, self.z)
    }
}

// Generic function with lifetime parameters
fn find_longest_vector<'a>(vectors: &'a [Vector3D]) -> Option<&'a Vector3D> {
    vectors.iter().max_by(|a, b| a.magnitude().partial_cmp(&b.magnitude()).unwrap())
}

// Trait for objects that can be transformed
trait Transformable {
    fn scale(&mut self, factor: f64);
    fn translate(&mut self, offset: &Vector3D);
}

impl Transformable for Vector3D {
    fn scale(&mut self, factor: f64) {
        self.x *= factor;
        self.y *= factor;
        self.z *= factor;
    }
    
    fn translate(&mut self, offset: &Vector3D) {
        self.x += offset.x;
        self.y += offset.y;
        self.z += offset.z;
    }
}

fn main() {
    let mut vectors = vec![
        Vector3D::new(1.0, 2.0, 3.0),
        Vector3D::new(4.0, 5.0, 6.0),
        Vector3D::new(0.0, 0.0, 0.0),
    ];
    
    println!("Original vectors:");
    for (i, vec) in vectors.iter().enumerate() {
        println!("Vector {}: {} (magnitude: {:.2})", i, vec, vec.magnitude());
    }
    
    // Find longest vector
    if let Some(longest) = find_longest_vector(&vectors) {
        println!("\nLongest vector: {}", longest);
    }
    
    // Test normalization with error handling
    for vec in &vectors {
        match vec.normalize() {
            Ok(normalized) => println!("Normalized {}: {}", vec, normalized),
            Err(e) => println!("Error normalizing {}: {}", vec, e),
        }
    }
    
    // Test vector operations
    let v1 = &vectors[0];
    let v2 = &vectors[1];
    
    println!("\nVector operations:");
    println!("Dot product: {:.2}", v1.dot_product(v2));
    println!("Cross product: {}", v1.cross_product(v2));
    
    // Test transformations
    let offset = Vector3D::new(1.0, 1.0, 1.0);
    vectors[0].scale(2.0);
    vectors[0].translate(&offset);
    println!("Transformed vector 0: {}", vectors[0]);
}
