import random
import math

def create_snowflake(seed, size=21):
    print(f"Seed: {seed}, Size: {size}")
    random.seed(seed)
    grid = [[' ' for _ in range(size)] for _ in range(size)]
    print(f"Initial grid: {[''.join(row) for row in grid]}")
    mid = size // 2
    print(f"Midpoint: {mid}")
    points = []

    # Generate points in one twelfth of the snowflake
    num_points = random.randint(5, 15)
    print(f"Number of points to generate in one twelfth: {num_points}")
    for i in range(num_points):
        r = random.randint(1, mid - 1)
        angle = random.uniform(0, math.pi / 6)  # 30 degrees slice
        x = int(mid + r * math.cos(angle))
        y = int(mid - r * math.sin(angle))
        char = random.choice(['*', '+', 'x', '|', '/', '\\'])
        points.append((x, y, char))
        print(f"Point {i}: r={r}, angle={angle:.2f}, x={x}, y={y}, char='{char}'")
    print(f"Generated points: {points}")

    def rotate(x, y, cx, cy, angle):
        dx, dy = x - cx, y - cy
        rx = dx * math.cos(angle) - dy * math.sin(angle)
        ry = dx * math.sin(angle) + dy * math.cos(angle)
        result = int(round(cx + rx)), int(round(cy + ry))
        print(f"Rotating ({x},{y}) around ({cx},{cy}) by {angle} radians -> {result}")
        return result

    # Apply 6-fold symmetry
    for idx, (dx, dy, char) in enumerate(points):
        print(f"Applying symmetry for point {idx}: ({dx},{dy},'{char}')")
        for i in range(6):
            angle = math.radians(i * 60)
            x_rot, y_rot = rotate(dx, dy, mid, mid, angle)
            if 0 <= x_rot < size and 0 <= y_rot < size:
                grid[y_rot][x_rot] = char
                print(f" Placed '{char}' at ({x_rot},{y_rot})")
            # Mirror over horizontal axis
            y_mirror = 2 * mid - y_rot
            if 0 <= x_rot < size and 0 <= y_mirror < size:
                grid[y_mirror][x_rot] = char
                print(f" Placed '{char}' at mirror ({x_rot},{y_mirror})")

    print("Final grid:")
    for row in grid:
        print(''.join(row))
    return '\n'.join(''.join(row) for row in grid)

# Example usage
if __name__ == '__main__':
    seed = input("Enter seed: ")
    print(create_snowflake(seed))
