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

heart_image = pygame.image.load("main_images/heart.png").convert_alpha()  # Замените на путь к вашему изображению сердца
heart_image = pygame.transform.scale(heart_image, (30, 30))  # Изменяем размер изображения сердца


# Загрузка изображений бонусов
shield_image = pygame.image.load("boosts/shield.png").convert_alpha()  # Замените на путь к вашему изображению щита
boost_image = pygame.image.load("boosts/boost.png").convert_alpha()  # Замените на путь к вашему изображению ускорения

# Изменим размер изображений для бонусов
BONUS_SCALE = 0.1  # Множитель для изменения размера (например, 10% от исходного размера)
shield_image = pygame.transform.scale(shield_image, (int(shield_image.get_width() * BONUS_SCALE),
                                                     int(shield_image.get_height() * BONUS_SCALE)))
boost_image = pygame.transform.scale(boost_image, (int(boost_image.get_width() * BONUS_SCALE),
                                                    int(boost_image.get_height() * BONUS_SCALE)))

game_paused = False  # Переменная для отслеживания состояния паузы

# Загрузка звука потери жизни
lose_life_sound = pygame.mixer.Sound("lose_life.mp3.wav")  # Замените на путь к вашему звуку

def load_and_scale_sprites(sprite_names, scale_factor):
    return [pygame.transform.scale(pygame.image.load(name).convert_alpha(),
                                    (int(pygame.image.load(name).get_width() * scale_factor),
                                     int(pygame.image.load(name).get_height() * scale_factor)))
            for name in sprite_names]

scale_factor = 2  # Увеличиваем в 2 раза
walk_right_sprites = load_and_scale_sprites([f"image_cat/walk_right_{i}.png" for i in range(1, 4)], scale_factor)
walk_left_sprites = load_and_scale_sprites([f"image_cat/walk_left_{i}.png" for i in range(1, 4)], scale_factor)
walk_up_sprites = load_and_scale_sprites([f"image_cat/walk_up_{i}.png" for i in range(1, 4)], scale_factor)
walk_down_sprites = load_and_scale_sprites([f"image_cat/walk_down_{i}.png" for i in range(1, 4)], scale_factor)

# Параметры анимации
current_frame = 0
frame_counter = 0
frame_rate = 10

# Параметры игры
score = 0
high_score = 0  # Переменная для хранения лучшего счёта
font = pygame.font.SysFont("monospace", 35)

# Загрузка фонового изображения
background = pygame.image.load("main_images/background.png").convert()

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
def draw_bonuses():
    for bonus in bonuses:
        if bonus[2] == "shield":
            screen.blit(shield_image, (bonus[0], bonus[1]))
        elif bonus[2] == "speed_boost":
            screen.blit(boost_image, (bonus[0], bonus[1]))

# Функция для создания бонусов с редкой вероятностью
# Счетчик кадров для создания бонусов
bonus_creation_timer = 0
BONUS_CREATION_INTERVAL = 120  # Количество кадров до появления нового бонуса

def create_bonus():
    x_pos = random.randint(0, WIDTH - BONUS_SIZE)
    y_pos = 0  # Бонус будет появляться сверху
    bonus_type = random.choice(["shield", "speed_boost"])

    # Добавляем бонус в список
    bonuses.append([x_pos, y_pos, bonus_type])


# Функция для обновления бонусов с параметрами
def update_bonuses(shield_active, shield_duration, speed_boost_active, speed_boost_duration):
    if shield_active:
        shield_duration -= 1
        if shield_duration <= 0:
            shield_active = False

    if speed_boost_active:
        speed_boost_duration -= 1
        if speed_boost_duration <= 0:
            speed_boost_active = False

    return shield_active, shield_duration, speed_boost_active, speed_boost_duration


# Использование
shield_active, shield_duration, speed_boost_active, speed_boost_duration = update_bonuses(
    shield_active, shield_duration, speed_boost_active, speed_boost_duration
)


# Функция создания бонусов на старте
def create_bonuses_on_start():
    for _ in range(1):  # Примерное количество бонусов на старте
        create_bonus()


# Отображаем таймер для бонусов
def draw_bonus_timer():
    # Таймер для щита
    if shield_active:
        timer_text = font.render(f"Щит: {shield_duration // 60}", True, BLUE)  # Показываем оставшееся время в секундах
        screen.blit(timer_text, (WIDTH - 150, HEIGHT - 40))  # Отображаем таймер щита справа внизу

    # Таймер для ускорения
    if speed_boost_active:
        timer_text = font.render(f"УСКР: {speed_boost_duration // 60}", True, RED)  # Показываем оставшееся время в секундах
        screen.blit(timer_text, (WIDTH - 150, HEIGHT - 70))  # Отображаем таймер ускорения чуть выше




def update_player_speed():
    global player_speed, speed_boost_active, speed_boost_duration
    if speed_boost_active:
        player_speed = 10  # Увеличиваем скорость в 2 раза (или любой другой множитель)
        speed_boost_duration -= 1  # Уменьшаем продолжительность ускорения
        if speed_boost_duration <= 0:
            speed_boost_active = False  # Останавливаем ускорение, когда время истечет
    else:
        player_speed = 5  # Обычная скорость




# Функция для обновления бонусов
def update_bonuses():
    global shield_active, shield_duration, speed_boost_active, speed_boost_duration

    # Уменьшаем вероятность появления бонуса
    if random.randint(1, 300) == 1:  # Уменьшаем вероятность появления бонуса (например, 1 из 100)
        create_bonus()  # Создаем бонус

    for bonus in bonuses:
        bonus[1] += 3  # Двигаем бонус вниз

        # Проверка на столкновение с игроком
        if check_collision(player_pos, bonus[:2]):
            if bonus[2] == "shield":
                shield_active = True
                shield_duration = 300  # Примерно 5 секунд (300 кадров)
            elif bonus[2] == "speed_boost":
                speed_boost_active = True
                speed_boost_duration = 300  # Примерно 5 секунд (300 кадров)
            bonuses.remove(bonus)

        # Если бонус выходит за пределы экрана, удаляем его
        if bonus[1] > HEIGHT:
            bonuses.remove(bonus)

    # Окончание действия бонусов
    if shield_active:
        shield_duration -= 1
        if shield_duration <= 0:
            shield_active = False

    if speed_boost_active:
        speed_boost_duration -= 1
        if speed_boost_duration <= 0:
            speed_boost_active = False


# Рисуем игрока
def draw_player(direction):
    global current_frame
    if direction == "right":
        screen.blit(walk_right_sprites[current_frame], (player_pos[0], player_pos[1]))
    elif direction == "left":
        screen.blit(walk_left_sprites[current_frame], (player_pos[0], player_pos[1]))
    elif direction == "up":
        screen.blit(walk_up_sprites[current_frame], (player_pos[0], player_pos[1]))
    elif direction == "down":
        screen.blit(walk_down_sprites[current_frame], (player_pos[0], player_pos[1]))

    # Нарисовать голубую окружность, если щит активен (смещаем вправо и вниз)
    if shield_active:
        pygame.draw.circle(screen, (0, 191, 255), (player_pos[0] + player_size // 2 + 15, player_pos[1] + player_size // 2 + 15),
                           player_size * 1.5, 3)  # Голубая окружность вокруг кота, смещена вправо и вниз


def toggle_pause():
    global game_paused
    game_paused = not game_paused


# Функция для отображения паузы
def draw_pause_screen():
    pause_text = font.render("Пауза! Нажмите пробел для продолжения", True, GREEN)
    screen.blit(pause_text, (WIDTH // 2 - pause_text.get_width() // 2, HEIGHT // 2 - 50))
    pygame.display.flip()

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
    global player_pos, score, enemies, current_frame, frame_counter, enemy_speed, enemy_spawn_rate, lives, bonuses, player_speed, shield_active, game_paused
    player_pos = [WIDTH // 2, HEIGHT // 2]
    score = 0
    lives = 3
    enemies.clear()
    bonuses = []  # Очистка бонусов перед началом игры

    if game_level == "easy":
        enemy_speed = 3
        enemy_spawn_rate = 30
    else:  # "hard"
        enemy_speed = 6
        enemy_spawn_rate = 15

    # Создаем бонусы на старте
    create_bonuses_on_start()

    clock = pygame.time.Clock()
    space_pressed = False  # Флаг для предотвращения многократных нажатий пробела
    direction = "right"  # Начальное направление

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        keys = pygame.key.get_pressed()

        # Проверка на пробел для паузы/продолжения
        if keys[pygame.K_SPACE]:
            if not space_pressed:  # Если пробел только что был нажат
                toggle_pause()  # Переключаем состояние паузы
                space_pressed = True  # Устанавливаем флаг

        if not keys[pygame.K_SPACE]:
            space_pressed = False  # Если пробел больше не удерживается, сбрасываем флаг

        if game_paused:
            # Когда игра на паузе, рисуем экран паузы
            draw_pause_screen()
            pygame.display.flip()
            continue  # Если игра на паузе, пропускаем остальную логику

        # Если игра не на паузе:
        # Движение игрока
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

        # Обновляем врагов и бонусы
        update_enemies()
        update_bonuses()
        update_player_speed()

        # Периодически создаём бонусы
        if random.randint(1, 100) == 1:  # На самом деле здесь можно настроить вероятность появления
            create_bonus()

        # Обработка столкновений с врагами
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

        # Обновляем анимацию
        frame_counter += 1
        if frame_counter >= frame_rate:
            if direction == "right":
                current_frame = (current_frame + 1) % len(walk_right_sprites)
            elif direction == "left":
                current_frame = (current_frame + 1) % len(walk_left_sprites)
            elif direction == "up":
                current_frame = (current_frame + 1) % len(walk_up_sprites)
            elif direction == "down":
                current_frame = (current_frame + 1) % len(walk_down_sprites)
            frame_counter = 0

        # Отображаем всё на экране
        screen.blit(background, (0, 0))

        # Рисуем игрока
        draw_player(direction)  # Передаем текущее направление

        # Рисуем врагов
        for enemy in enemies:
            pygame.draw.circle(screen, enemy[3], (enemy[0], enemy[1]), enemy_size // 2)

        # Рисуем бонусы
        draw_bonuses()

        # Рисуем таймер для бонусов
        draw_bonus_timer()

        # Отображаем жизни
        for i in range(lives):
            screen.blit(heart_image, (10 + i * 35, HEIGHT - 40))

        # Отображаем счёт
        score_text = font.render("Счёт: " + str(score), True, GREEN)
        screen.blit(score_text, (10, 10))

        pygame.display.flip()
        clock.tick(30)

# Запускаем игру
def main():
    global high_score
    init_db()  # Инициализация БД
    high_score = load_high_score()  # Загрузка лучшего счёта

    # Загрузка и воспроизведение музыки
    pygame.mixer.music.load("music/background_music.mp3")
    pygame.mixer.music.set_volume(0.5)  # Устанавливаем громкость (от 0.0 до 1.0)
    pygame.mixer.music.play(-1)  # Воспроизводим музыку бесконечно

    start_screen()  # Начинаем с начального экрана
    game_loop()  # Запускаем основной цикл


if __name__ == "__main__":
    main()