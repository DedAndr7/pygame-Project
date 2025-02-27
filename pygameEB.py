import pygame
import random
import sys
import sqlite3

# Инициализация Pygame
pygame.init()

# Настройки окна
WIDTH, HEIGHT = 1200, 873
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Кошки")

# Цвета
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)

# Параметры игрока
player_size = 30
player_pos = [WIDTH // 2, HEIGHT // 2]
player_speed = 5
lives = 3  # Количество жизней

# Параметры бонусов
BONUS_SIZE = 45
shield_active = False
shield_duration = 0
speed_boost_active = False
speed_boost_duration = 0
bonuses = []

# Параметры врагов
enemy_size = 30
enemy_spawn_rate = 20  # Вероятность появления врагов
enemy_speed = 5
enemies = []

heart_image = pygame.image.load("heart.png").convert_alpha()  # Замените на путь к вашему изображению сердца
heart_image = pygame.transform.scale(heart_image, (30, 30))  # Изменяем размер изображения сердца

# Загрузка изображений врага
enemy_image = pygame.image.load("enemy_image.png").convert_alpha()  # Замените на путь к вашему изображению врага
enemy_image = pygame.transform.scale(enemy_image, (enemy_size, enemy_size))  # Изменяем размер изображения

# Загрузка звука потери жизни
lose_life_sound = pygame.mixer.Sound("lose_life.mp3.wav")  # Замените на путь к вашему звуку

def load_and_scale_sprites(sprite_names, scale_factor):
    return [pygame.transform.scale(pygame.image.load(name).convert_alpha(),
                                    (int(pygame.image.load(name).get_width() * scale_factor),
                                     int(pygame.image.load(name).get_height() * scale_factor)))
            for name in sprite_names]

scale_factor = 2  # Увеличиваем в 2 раза
walk_right_sprites = load_and_scale_sprites([f"walk_right_{i}.png" for i in range(1, 4)], scale_factor)
walk_left_sprites = load_and_scale_sprites([f"walk_left_{i}.png" for i in range(1, 4)], scale_factor)
walk_up_sprites = load_and_scale_sprites([f"walk_up_{i}.png" for i in range(1, 4)], scale_factor)
walk_down_sprites = load_and_scale_sprites([f"walk_down_{i}.png" for i in range(1, 4)], scale_factor)

# Параметры анимации
current_frame = 0
frame_counter = 0
frame_rate = 10

# Параметры игры
score = 0
high_score = 0  # Переменная для хранения лучшего счёта
font = pygame.font.SysFont("monospace", 35)

# Загрузка фонового изображения
background = pygame.image.load("background.png").convert()

# Переменная для уровня сложности
game_level = "easy"  # По умолчанию уровень легкий


# Подключение к БД
def init_db():
    conn = sqlite3.connect('game_scores.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS scores
                      (id INTEGER PRIMARY KEY, score INTEGER)''')
    conn.commit()
    conn.close()


# Сохранение лучшего счёта в БД
def save_score(new_score):
    conn = sqlite3.connect('game_scores.db')
    cursor = conn.cursor()
    cursor.execute('SELECT MAX(score) FROM scores')
    max_score = cursor.fetchone()[0]

    if max_score is None or new_score > max_score:
        cursor.execute('INSERT INTO scores (score) VALUES (?)', (new_score,))
        conn.commit()

    conn.close()


# Загрузка лучшего счёта из БД
def load_high_score():
    conn = sqlite3.connect('game_scores.db')
    cursor = conn.cursor()
    cursor.execute('SELECT MAX(score) FROM scores')
    max_score = cursor.fetchone()[0]

    if max_score is not None:
        return max_score
    return 0


# Создание бонусов
def create_bonus():
    bonus_type = random.choice(["shield", "speed_boost"])
    x_pos = random.randint(0, WIDTH - BONUS_SIZE)
    y_pos = 0
    color = random.choice([CYAN, ORANGE])  # Цвет для бонусов (можно использовать фиксированные цвета для бонусов)

    if bonus_type == "shield":
        bonuses.append([x_pos, y_pos, bonus_type, (0, 0, 139)])  # Темно-синий цвет для щита
    elif bonus_type == "speed_boost":
        bonuses.append([x_pos, y_pos, bonus_type, (128, 0, 128)])  # Фиолетовый цвет для ускорения


# Обновление бонусов
# Update bonuses (unchanged)
def update_bonuses():
    global shield_active, shield_duration, speed_boost_active, speed_boost_duration

    for bonus in bonuses:
        bonus[1] += 3  # Move bonuses down the screen

        # Check for collision with player
        if check_collision(player_pos, bonus[:2]):
            if bonus[2] == "shield":
                shield_active = True
                shield_duration = 300
            elif bonus[2] == "speed_boost":
                speed_boost_active = True
                speed_boost_duration = 300
            bonuses.remove(bonus)

        if bonus[1] > HEIGHT:
            bonuses.remove(bonus)

    if shield_active:
        shield_duration -= 1
        if shield_duration <= 0:
            shield_active = False

    if speed_boost_active:
        speed_boost_duration -= 1
        if speed_boost_duration <= 0:
            speed_boost_active = False


def draw_bonuses():
    for bonus in bonuses:
        # Check the type of bonus and draw accordingly
        if bonus[2] == "shield":
            # Dark blue box for shield
            pygame.draw.rect(screen, (0, 0, 139), pygame.Rect(bonus[0], bonus[1], BONUS_SIZE, BONUS_SIZE // 2))

        elif bonus[2] == "speed_boost":
            # Purple box for speed boost
            pygame.draw.rect(screen, (128, 0, 128), pygame.Rect(bonus[0], bonus[1], BONUS_SIZE, BONUS_SIZE // 2))



# Обновление скорости игрока
def update_player_speed():
    global player_speed
    if speed_boost_active:
        player_speed = 8  # Увеличенная скорость
    else:
        player_speed = 5  # Обычная скорость

# Функция создания бонуса
def create_bonus():
    # Генерация случайных координат для бонуса
    x = random.randint(0, WIDTH - BONUS_SIZE)
    y = random.randint(0, HEIGHT - BONUS_SIZE)

    # Случайный выбор типа бонуса (например, "shield" или "speed_boost")
    bonus_type = random.choice(["shield", "speed_boost"])

    # Добавление бонуса в список
    bonuses.append([x, y, bonus_type])


# Создание бонусов на старте
def create_bonuses_on_start():
    for _ in range(5):  # Примерное количество бонусов на старте
        create_bonus()


# Функция для создания врагов
def create_enemy():
    enemy_type = random.choice(["normal", "zigzag", "fast", "chaser", "spawner", "jumper"])
    x_pos = random.randint(0, WIDTH - enemy_size)
    y_pos = 0

    # Assign a unique color based on enemy type
    enemy_colors = {
        "normal": RED,
        "zigzag": GREEN,
        "fast": BLUE,
        "chaser": YELLOW,
        "spawner": CYAN,
        "jumper": ORANGE
    }

    color = enemy_colors.get(enemy_type, PURPLE)  # Default to PURPLE if no match is found

    enemies.append([x_pos, y_pos, enemy_type, color])


# Функция для обновления позиции врагов
def update_enemies():
    global score
    for enemy in enemies:
        if enemy[2] == "normal":
            enemy[1] += enemy_speed
        elif enemy[2] == "zigzag":
            enemy[1] += enemy_speed
            enemy[0] += random.choice([-1, 1]) * enemy_speed  # Move in zigzag pattern
        elif enemy[2] == "fast":
            enemy[1] += enemy_speed * 2  # Fast movement
        elif enemy[2] == "chaser":
            if player_pos[0] < enemy[0]:
                enemy[0] -= enemy_speed // 2
            elif player_pos[0] > enemy[0]:
                enemy[0] += enemy_speed // 2
            if player_pos[1] < enemy[1]:
                enemy[1] -= enemy_speed // 2
            elif player_pos[1] > enemy[1]:
                enemy[1] += enemy_speed // 2
        elif enemy[2] == "spawner":
            enemy[1] += enemy_speed
            if random.randint(1, 100) == 1:  # Spawn a new enemy from this enemy
                create_enemy()
        elif enemy[2] == "jumper":
            if random.randint(1, 100) == 1:  # Jump at a random moment
                enemy[1] -= 50
            else:
                enemy[1] += enemy_speed
        if enemy[1] > HEIGHT:
            enemies.remove(enemy)
            score += 1
    if random.randint(1, enemy_spawn_rate) == 1:
        create_enemy()


# Функция для проверки столкновений
def check_collision(player_poss, enemy_pos):
    p_x, p_y = player_poss
    e_x, e_y = enemy_pos
    if (e_x >= p_x and e_x < (p_x + player_size)) or (p_x >= e_x and p_x < (e_x + enemy_size)):
        if (e_y >= p_y and e_y < (p_y + player_size)) or (p_y >= e_y and p_y < (e_y + enemy_size)):
            return True
    return False


# Функция выбора уровня сложности
def level_selection():
    global game_level
    while True:
        screen.blit(background, (0, 0))
        title_text = font.render("Выберите уровень сложности", True, GREEN)
        easy_text = font.render("1. Легкий", True, BLUE)
        hard_text = font.render("2. Сложный", True, BLUE)

        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 2 - 50))
        screen.blit(easy_text, (WIDTH // 2 - easy_text.get_width() // 2, HEIGHT // 2))
        screen.blit(hard_text, (WIDTH // 2 - hard_text.get_width() // 2, HEIGHT // 2 + 50))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    game_level = "easy"
                    return
                elif event.key == pygame.K_2:
                    game_level = "hard"
                    return


# Функция начального окна
def start_screen():
    while True:
        screen.blit(background, (0, 0))
        title_text = font.render("Добро пожаловать в игру!", True, GREEN)
        instructions_text = font.render("Нажмите любую клавишу для начала", True, BLUE)
        score_text = font.render(f"Лучший счёт: {high_score}", True, RED)

        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 2 - 50))
        screen.blit(instructions_text, (WIDTH // 2 - instructions_text.get_width() // 2, HEIGHT // 2 + 10))
        screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2 + 50))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                level_selection()  # Переход к выбору уровня сложности
                return  # Переход к игровому циклу


# Функция конечного окна
def end_screen():
    while True:
        screen.blit(background, (0, 0))
        final_text = font.render("Игра окончена!", True, RED)
        score_text = font.render(f"Ваш счёт: {score}", True, BLUE)
        high_score_text = font.render(f"Лучший счёт: {high_score}", True, GREEN)
        restart_text = font.render("Нажмите R для перезапуска или Q для выхода", True, GREEN)

        screen.blit(final_text, (WIDTH // 2 - final_text.get_width() // 2, HEIGHT // 2 - 50))
        screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2))
        screen.blit(high_score_text, (WIDTH // 2 - high_score_text.get_width() // 2, HEIGHT // 2 + 50))
        screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 100))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    main()  # Начинаем новую игру
                    return
                if event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()


def game_loop():
    global player_pos, score, enemies, current_frame, frame_counter, enemy_speed, enemy_spawn_rate, lives, bonuses, player_speed, shield_active
    player_pos = [WIDTH // 2, HEIGHT // 2]
    score = 0
    lives = 3
    enemies.clear()
    bonuses = []  # Ensure bonuses list is initialized

    direction = "right"

    if game_level == "easy":
        enemy_speed = 3
        enemy_spawn_rate = 30
    else:  # "hard"
        enemy_speed = 6
        enemy_spawn_rate = 15

    clock = pygame.time.Clock()  # Initialize clock once

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] and player_pos[0] > 0:
            player_pos[0] -= player_speed
            direction = "left"
        if keys[pygame.K_d] and player_pos[0] < WIDTH - player_size:
            player_pos[0] += player_speed
            direction = "right"
        if keys[pygame.K_w] and player_pos[1] > 0:
            player_pos[1] -= player_speed
            direction = "up"
        if keys[pygame.K_s] and player_pos[1] < HEIGHT - player_size:
            player_pos[1] += player_speed
            direction = "down"

        update_enemies()
        update_bonuses()  # Update bonuses
        update_player_speed()  # Update player speed

        # Handle collisions with enemies
        for enemy in enemies:
            if check_collision(player_pos, enemy[:2]):
                if shield_active:
                    enemies.remove(enemy)
                else:
                    lives -= 1
                    lose_life_sound.play()
                    if lives == 0:
                        save_score(score)
                        end_screen()
                    enemies.remove(enemy)
                break

        # Draw everything
        screen.blit(background, (0, 0))

        # Draw player based on direction
        if direction == "right":
            screen.blit(walk_right_sprites[current_frame], (player_pos[0], player_pos[1]))
        elif direction == "left":
            screen.blit(walk_left_sprites[current_frame], (player_pos[0], player_pos[1]))
        elif direction == "up":
            screen.blit(walk_up_sprites[current_frame], (player_pos[0], player_pos[1]))
        elif direction == "down":
            screen.blit(walk_down_sprites[current_frame], (player_pos[0], player_pos[1]))

        # Draw enemies
        for enemy in enemies:
            pygame.draw.circle(screen, enemy[3], (enemy[0], enemy[1]), enemy_size // 2)

        # Draw bonuses
        draw_bonuses()

        # Отображение жизней
        for i in range(lives):
            screen.blit(heart_image, (10 + i * 35, HEIGHT - 40))  # Рисуем сердца в левом нижнем углу

        # Display score
        score_text = font.render("Счёт: " + str(score), True, GREEN)
        screen.blit(score_text, (10, 10))

        pygame.display.flip()
        clock.tick(30)  # Limiting frame rate



# Запускаем игру
def main():
    global high_score
    init_db()  # Инициализация БД
    high_score = load_high_score()  # Загрузка лучшего счёта

    # Загрузка и воспроизведение музыки
    pygame.mixer.music.load("background_music.mp3")
    pygame.mixer.music.set_volume(0.5)  # Устанавливаем громкость (от 0.0 до 1.0)
    pygame.mixer.music.play(-1)  # Воспроизводим музыку бесконечно

    start_screen()  # Начинаем с начального экрана
    game_loop()  # Запускаем основной цикл


if __name__ == "__main__":
    main()
