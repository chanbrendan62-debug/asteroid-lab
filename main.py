
import random
import math
import pygame
import asyncio

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
dt = 0


class Asteroid:

    def __init__(self):
        self.radius = random.randint(10, 40)
        speed = 50 / self.radius

        self.pos = pygame.math.Vector2(
            random.randint(self.radius, WIDTH - self.radius),
            random.randint(self.radius, HEIGHT - self.radius),
        )

        self.vel = (
            pygame.math.Vector2(
                random.uniform(-1, 1), random.uniform(-1, 1)
            ).normalize()
            * speed
        )

        self.mass = self.radius**2

    def update(self):
        self.pos += self.vel

        if self.pos.x > WIDTH:
            self.pos.x = 0

        if self.pos.x < 0:
            self.pos.x = WIDTH

        if self.pos.y > HEIGHT:
            self.pos.y = 0

        if self.pos.y < 0:
            self.pos.y = HEIGHT

    def draw(self, surface):
        pygame.draw.circle(
            surface,
            (128, 128, 128),
            (int(self.pos.x), int(self.pos.y)),
            self.radius,
        )

def respawn(player_pos, min_distance=150):
    while True:
        pos = pygame.math.Vector2(
            random.randint(40, WIDTH - 40),
            random.randint(40, HEIGHT - 40)
        )
        if pos.distance_to(player_pos) > min_distance:
            asteroid = Asteroid()
            asteroid.pos = pos
            return asteroid


class Missile:

    def __init__(self, start_pos, target_pos):
        self.pos = pygame.math.Vector2(start_pos)
        self.speed = 8

        direction = target_pos - self.pos
        if direction.length() > 0:
            self.vel = direction.normalize() * self.speed
        else:
            self.vel = pygame.math.Vector2(0, -1) * self.speed

    def update(self):
        self.pos += self.vel

    def draw(self, surface):
        pygame.draw.rect(
            surface, (255, 255, 255), (int(self.pos.x), int(self.pos.y), 4, 7)
        )


class Player:

    def __init__(self):
        self.pos = pygame.math.Vector2(WIDTH // 2, HEIGHT // 2)
        self.angle = 90
        self.rotation = 4
        self.maxspd = 400
        self.velocity = pygame.Vector2(0, 0)
        self.acceleration = pygame.Vector2(0, 0)
        self.thrust = 750
        self.drag = 0.98

    def get_forward(self):
        radians = math.radians(self.angle)
        return pygame.Vector2(math.cos(radians), -math.sin(radians))

    def draw(self, surface):
        forward = self.get_forward()
        left = forward.rotate(140)
        right = forward.rotate(-140)

        p1 = self.pos + forward * 22
        p2 = self.pos + left * 16
        p3 = self.pos + right * 16

        pygame.draw.polygon(screen, "green", [p1, p2, p3], 2)

    def update(self):
        self.velocity += self.acceleration * dt
        if self.pos.x > WIDTH:
            self.pos.x = 0
        if self.pos.x < 0:
            self.pos.x = WIDTH
        if self.pos.y > HEIGHT:
            self.pos.y = 0
        if self.pos.y < 0:
            self.pos.y = HEIGHT
        
        if self.velocity.length() > self.maxspd:
            self.velocity.scale_to_length(self.maxspd)

        self.velocity *= self.drag
        self.pos += self.velocity * dt


class Enemy:

    def __init__(self):
        self.pos = pygame.Vector2(WIDTH // 4, HEIGHT // 2)
        self.vel = pygame.Vector2(0, 0)
        self.angle = 0
        self.rotation = 4
        self.detection_range = 200
        self.fov = 0.7
        self.color = (255, 255, 255)
        self.random_rotate = random.randint(-2, 2)

    def get_forward(self):
        radians = math.radians(self.angle)
        return pygame.Vector2(math.cos(radians), -math.sin(radians))

    def draw(self, surface):
        forward = self.get_forward()
        left = forward.rotate(140)
        right = forward.rotate(-140)

        p1 = self.pos + forward * 22
        p2 = self.pos + left * 16
        p3 = self.pos + right * 16

        pygame.draw.polygon(screen, self.color, [p1, p2, p3], 2)
        pygame.draw.circle(screen, "gray", self.pos, self.detection_range, 1)
        pygame.draw.line(screen, "red", self.pos, self.pos + forward * 100, 3)

    def update(self, player):
        to_player = player.pos - self.pos
        distance = self.pos.distance_to(player.pos)

        if to_player.length() > 0:
            to_player = to_player.normalize()

        dot = self.get_forward().dot(to_player)

        if distance < self.detection_range and dot > self.fov:
            self.color = (255, 0, 0)
            self.vel += to_player * 150 * dt
        else:
            self.color = (255, 255, 255)
            self.vel *= 0.95
            self.angle = (self.angle + self.random_rotate) % 360

        self.pos += self.vel * dt


def bounce(a1, a2):
    distance_vec = a1.pos - a2.pos
    distance = distance_vec.length()

    min_distance = a1.radius + a2.radius

    if distance < min_distance and distance > 0:
        overlap = min_distance - distance
        direction = distance_vec.normalize()
        a1.pos += direction * (overlap / 2)
        a2.pos -= direction * (overlap / 2)

        total_mass = a1.mass + a2.mass

        new_vel1 = (
            a1.vel * (a1.mass - a2.mass) + (2 * a2.mass * a2.vel)
        ) / total_mass
        new_vel2 = (
            a2.vel * (a2.mass - a1.mass) + (2 * a1.mass * a1.vel)
        ) / total_mass

        a1.vel = new_vel1
        a2.vel = new_vel2


asteroids = [Asteroid() for _ in range(6)]
player = Player()
missiles = []
enemy = Enemy()


async def main():
    global dt
    running = True
    while running:
        player.acceleration = pygame.Vector2(0, 0)

        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT]:
            player.angle += player.rotation

        if keys[pygame.K_RIGHT]:
            player.angle -= player.rotation

        if keys[pygame.K_UP]:
            player.acceleration = player.get_forward() * player.thrust

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    target_pos = pygame.math.Vector2(event.pos)
                    missiles.append(Missile(player.pos, target_pos))

        for asteroid in asteroids:
            asteroid.update()

        for i in range(len(asteroids)):
            for j in range(i + 1, len(asteroids)):
                bounce(asteroids[i], asteroids[j])

        for missile in missiles[:]:
            missile.update()
            if (
                missile.pos.x < 0
                or missile.pos.x > WIDTH
                or missile.pos.y < 0
                or missile.pos.y > HEIGHT
            ):
                missiles.remove(missile)


        for missile in missiles[:]:
            for asteroid in asteroids[:]:
                if missile.pos.distance_to(asteroid.pos) < asteroid.radius:
                    if missile in missiles:
                        missiles.remove(missile)
                    if asteroid in asteroids:
                        asteroids.remove(asteroid)
                   
                    asteroids.append(respawn(player.pos))
                    break
        screen.fill((30, 30, 30))

        for asteroid in asteroids:
            asteroid.draw(screen)

        player.update()
        enemy.update(player)
        player.draw(screen)
        enemy.draw(screen)

        for missile in missiles:
            missile.draw(screen)

        pygame.display.flip()
        dt = clock.tick(60) / 1000.0
        await asyncio.sleep(0)

    pygame.quit()


asyncio.run(main())
