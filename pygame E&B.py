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

# Параметры врагов
enemy_size = 30
enemy_spawn_rate = 20  # Вероятность появления врагов
enemy_speed = 5
enemies = []

# Загрузка изображений врага
enemy_image = pygame.image.load("enemy_image.png").convert_alpha()  # Замените на путь к вашему изображению врага
enemy_image = pygame.transform.scale(enemy_image, (enemy_size, enemy_size))  # Изменяем размер изображения

# Загрузка звука потери жизни
lose_life_sound = pygame.mixer.Sound("lose_life.mp3.wav")  # Замените на путь к вашему звуку

# Загрузка анимации игрока
walk_right_sprites = [pygame.image.load(f"walk_right_{i}.png").convert_alpha() for i in
                      range(1, 4)]  # Изображения для движения вправо
walk_left_sprites = [pygame.image.load(f"walk_left_{i}.png").convert_alpha() for i in
                     range(1, 4)]  # Изображения для движения влево
walk_up_sprites = [pygame.image.load(f"walk_up_{i}.png").convert_alpha() for i in
                   range(1, 4)]  # Изображения для движения вверх
walk_down_sprites = [pygame.image.load(f"walk_down_{i}.png").convert_alpha() for i in
                     range(1, 4)]  # Изображения для движения вниз

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


# Функция для создания врагов
def create_enemy():
    enemy_type = random.choice(["normal", "zigzag", "fast", "chaser", "spawner", "jumper"])
    x_pos = random.randint(0, WIDTH - enemy_size)
    y_pos = 0
    color = random.choice([RED, GREEN, BLUE, YELLOW, CYAN, ORANGE, PURPLE])  # Random color for the enemy circle
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


# Основной игровой цикл
def game_loop():
    global player_pos, score, enemies, current_frame, frame_counter, enemy_speed, enemy_spawn_rate, lives
    player_pos = [WIDTH // 2, HEIGHT // 2]
    score = 0
    lives = 3  # Обнуляем жизни
    enemies.clear()  # Очищаем список врагов

    direction = "right"  # Направление движения игрока

    # Настройка параметров врагов в зависимости от уровня сложности
    if game_level == "easy":
        enemy_speed = 3  # Враги движутся медленнее
        enemy_spawn_rate = 30  # Враги появляются реже
    else:  # "hard"
        enemy_speed = 6  # Враги движутся быстрее
        enemy_spawn_rate = 15  # Враги появляются чаще

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

        for enemy in enemies:
            if check_collision(player_pos, enemy[:2]):
                lives -= 1  # Уменьшаем количество жизней
                lose_life_sound.play()  # Проигрываем звук потери жизни
                if lives == 0:  # Если жизни кончились
                    save_score(score)  # Сохранение счёта перед окончанием игры
                    end_screen()  # Переход к оконцу окончания игры

                enemies.remove(enemy)  # Убираем врага, который столкнулся с игроком
                break  # Прерываем цикл, чтобы избежать повторных столкновений

        # Обновляем анимацию
        frame_counter += 1
        if frame_counter >= frame_rate:
            current_frame = (current_frame + 1) % len(walk_right_sprites) if direction == "right" else \
                (current_frame + 1) % len(walk_left_sprites) if direction == "left" else \
                (current_frame + 1) % len(walk_up_sprites) if direction == "up" else \
                (current_frame + 1) % len(walk_down_sprites)

            frame_counter = 0

        # Рисуем фон
        screen.blit(background, (0, 0))

        # Рисуем игрока с анимацией в зависимости от направления
        if direction == "right":
            screen.blit(walk_right_sprites[current_frame], (player_pos[0], player_pos[1]))
        elif direction == "left":
            screen.blit(walk_left_sprites[current_frame], (player_pos[0], player_pos[1]))
        elif direction == "up":
            screen.blit(walk_up_sprites[current_frame], (player_pos[0], player_pos[1]))
        elif direction == "down":
            screen.blit(walk_down_sprites[current_frame], (player_pos[0], player_pos[1]))

        # Рисуем врагов как цветные круги
        for enemy in enemies:
            pygame.draw.circle(screen, enemy[3], (enemy[0], enemy[1]), enemy_size // 2)

        # Отображение жизней
        for i in range(lives):
            pygame.draw.rect(screen, RED, pygame.Rect(10 + i * 35, HEIGHT - 40, 30, 30))  # Рисуем жизни

        # Отображение счёта
        score_text = font.render("Счёт: " + str(score), True, GREEN)
        screen.blit(score_text, (10, 10))

        # Обновляем экран
        pygame.display.flip()
        pygame.time.Clock().tick(30)


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
