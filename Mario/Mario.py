import pygame
import math
import random
import time

prev_time = time.time()


pygame.init()

pygame.joystick.init()
joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]
for joystick in joysticks:
    joystick.init()
print joysticks

width = 256     # 16 tiles
height = 224    # 14 tiles
fps = 60
gravity = 1
friction = 3
sprinting_acceleration = 1.25
walking_acceleration = 0.75
jumping_acceleration = 1.00

shell_speed = 7.0
fireball_speed = 5.0
fireball_bounce_speed = 5.0
initial_falling_speed = -5

small_mario_height = 14
big_mario_height = 28

white = (255, 255, 255)
black = (0, 0, 0)

left_pressed = right_pressed = up_pressed = down_pressed = 0
space_pressed = False
allow_space_press = True
pressed_shift = False

clock = pygame.time.Clock()
Bricks = pygame.image.load("./Resources/Spritesheet/Bricks.png")
PipeShafts = pygame.image.load("./Resources/Spritesheet/PipeShafts.png")
PipeEnds = pygame.image.load("./Resources/Spritesheet/PipeEnds.png")
PipeConnectors = pygame.image.load("./Resources/Spritesheet/PipeConnectors.png")

mario_font = pygame.font.Font("./Resources/Font/mario_font.ttf", 9)

# (((frames % (A*fps/B))/(fps/B)) * 16, 0, 16, 16) ===> A is ammount of images, B is images/sec
# ((frames/fps*B) % A)*16


def sign(value):
    if value < 0:
        return -1
    else:
        return 1


def x_collision(obj1, obj2):
    if obj1[0] + obj1[2] > obj2[0] and obj1[0] < obj2[0] + obj2[2]:
        return True
    return False


def y_collision(obj1, obj2):
    if obj1[1] + obj1[3] > obj2[1] and obj1[1] < obj2[1] + obj2[3]:
        return True
    return False


def collision(obj1, obj2):
    # obj1, obj2: [x, y, width, height]
    if x_collision(obj1, obj2):
        if y_collision(obj1, obj2):
            return True
    return False


def allow_uncrouch():
    if mario.power > 0:
        checklist = []
        for x in range(int(mario.x)/16 - 2, int(mario.x)/16 + 3):  # [int(self.x)/16, int(self.x)/16 - 1, int(self.x)/16 + 1]:  #
            for y in range(int(mario.y)/16 - 6, int(mario.y)/16 + 3):
                if 0 <= y < len(screen.level.data) and 0 <= x < len(screen.level.data[y]):
                    if not isinstance(screen.level.data[y][x], str):
                        checklist.append(screen.level.data[y][x])
        if not any([collision([mario.x, mario.y - (big_mario_height - small_mario_height), mario.width, big_mario_height],
                              [checking.x, checking.y, checking.width, checking.height])
                    if checking.collision else False for checking in checklist]) and\
                not mario.y - (big_mario_height - small_mario_height) < 0:
            return True
        return False
    else:
        return True


class Popup(object):
    def __init__(self, x, y, text):
        self.x = x
        self.y = y
        self.text = mario_font.render(str(text), 1, white)
        self.frames = fps/6

    def update(self):
        self.y -= 1
        self.frames -= 1
        screen.complete.blit(self.text, (self.x, self.y))


class Camera(object):
    def __init__(self):
        self.x = 0
        self.y = 0
        self.fixed = False

    def move(self, dx):
        self.x += dx


class Particle(object):
    def __init__(self, x, y, xv, yv, tex):
        self.x = x
        self.y = y
        self.xv = xv
        self.yv = yv
        self.tex = tex

    def update(self):
        self.x += self.xv
        self.yv += gravity
        self.y += self.yv

        screen.complete.blit(self.tex, (self.x, self.y))


class MovingCoin(object):
    def __init__(self, x, y):
        self.initial_x = self.x = x
        self.initial_y = self.y = y
        self.yv = -8.0
        self.tex = pygame.image.load("./Resources/Spritesheet/MovingCoin.png")
        self.frame = 0

    def update(self):
        self.yv += gravity
        self.y += self.yv

        if frames % 2 == 0:
            self.frame = (self.frame + 1) % 4

        surface = pygame.Surface((16, 16))
        surface.blit(self.tex, (0, 0), (self.frame*16, 0, 16, 16))
        surface.set_colorkey((12, 12, 12))

        screen.complete.blit(surface, (self.x, self.y))


class StandingCoin(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.hit_box = [self.x + 3, self.y + 3, 10, 10]
        self.tex = pygame.image.load("./Resources/Spritesheet/Coins.png")

    def update(self):
        surface = pygame.Surface((16, 16))
        surface.blit(self.tex, (0, 0), ((4*frames/fps % 4) * 16, 0, 16, 16))
        surface.set_colorkey((1, 1, 1))

        screen.complete.blit(surface, (self.x, self.y))


class BasicAI(object):

    # contains basic movement (at the level of a mushroom)

    def __init__(self, x, y, yv=0.0, xv=-1.0, width=16, height=16, state="normal"):
        self.x = x
        self.y = y
        self.yv = yv
        self.xv = xv
        self.width = width
        self.height = height
        self.state = state
        self.tex = pygame.Surface((self.width, self.height))

    def move(self):
        checklist = []
        for x in range(int(self.x)/16 - 1, int(self.x)/16 + 2):
            for y in range(int(self.y)/16 - 1, int(self.y)/16 + 2):
                if 0 <= y < len(screen.level.data) and 0 <= x < len(screen.level.data[y]):
                    if not isinstance(screen.level.data[y][x], str):
                        checklist.append(screen.level.data[y][x])

        self.yv += gravity
        next_y = self.y + self.yv

        if next_y < 0:
            self.y = 0
            self.yv = 0.0
        else:
            allow_movement = True
            for checking in checklist:
                if checking.collision:
                    if collision([self.x, next_y, self.width, self.height],
                                 checking.collision_box):
                        if checking.state == "hit":
                            self.yv = checking.yv
                            next_y = self.y + self.yv
                        else:
                            allow_movement = False
                            if self.y < checking.y:
                                self.y = checking.y - self.height
                            else:
                                self.y = checking.y + checking.height
                                self.yv = 0.0
                            break

            if allow_movement:
                self.y = next_y
                if any([collision([self.x, self.y, self.width, self.height], tile.collision_box) if tile.collision else False for tile in checklist]):
                    self.yv = 0.0
            else:
                self.yv = 0.0

        next_x = self.x + self.xv

        allow_movement = True
        for checking in checklist:
            if checking.collision:
                if collision([next_x, self.y, self.width, self.height],
                             checking.collision_box):
                    if checking.breakable and type(self) == Shell:
                        checking.break_block()
                    allow_movement = False
                    self.xv *= -1
                    break

        if allow_movement:
            self.x = next_x


class Mushroom(BasicAI):
    def __init__(self, x, y):
        BasicAI.__init__(self, x, y + 16, xv=2.5, yv=0, state="appearing")
        self.target_y = y
        self.tex_large = pygame.image.load("./Resources/Spritesheet/Mushrooms.png")
        self.tex = pygame.Surface((16, 16))
        self.tex.blit(self.tex_large, (0, 0), (0, 0, 16, 16))
        self.tex.set_colorkey((1, 1, 1))

    def move(self):
        if self.state == "normal":
            BasicAI.move(self)

        elif self.state == "appearing":
            self.y -= 1
            if self.y == self.target_y:
                self.state = "normal"

    def update(self):
        self.move()
        screen.complete.blit(self.tex, (self.x, self.y))


class Goomba(BasicAI):
    def __init__(self, x, y):
        BasicAI.__init__(self, x, y, xv=-1.0, yv=0.0)
        self.width = 16
        self.height = 16
        self.tex = pygame.image.load("./Resources/Spritesheet/Goomba.png")
        self.collision_box = [self.x + 2, self.y + 2, 12, 12]
        self.alive = True
        self.corpse_frames = fps/8
        self.falling = False

    def update(self):
        surface = pygame.Surface((16, 16))
        if self.falling:
            self.yv += gravity
            self.y += self.yv
            surface.blit(self.tex, (0, 0), ((4*frames/fps % 2) * 16, 0, 16, 16))
            surface = pygame.transform.flip(surface, False, True)
        elif self.alive:
            self.move()
            self.collision_box = [self.x + 2, self.y + 2, 12, 12]
            surface.blit(self.tex, (0, 0), ((4*frames/fps % 2) * 16, 0, 16, 16))
        else:
            surface.blit(self.tex, (0, 0), (32, 0, 16, 16))
            self.corpse_frames -= 1
        surface.set_colorkey((1, 1, 1))
        screen.complete.blit(surface, (self.x, self.y))

    def get_hit(self):
        self.alive = False
        screen.popups.append(Popup(self.x, self.y - 16, 200 + mario.jumped_enemies*200))
        screen.ui.score += 200 + mario.jumped_enemies*200


class Shell(BasicAI):
    def __init__(self, x, y, x_dir, color, xv=0.0, yv=0.0):
        BasicAI.__init__(self, x, y, xv=xv, yv=float(yv))
        self.tex = pygame.image.load("./Resources/Spritesheet/Shell.png")
        self.collision_box = [self.x + 2, self.y + 2, 12, 12]
        self.color = color
        self.alive = True
        self.falling = False

    def update(self):
        surface = pygame.Surface((16, 16))
        if self.falling:
            self.yv += gravity
            self.y += self.yv
            surface.blit(self.tex, (0, 0), (0, ["green", "red"].index(self.color)*16, 16, 16))
            surface = pygame.transform.flip(surface, False, True)
        else:
            self.move()
            self.collision_box = [self.x + 2, self.y + 2, 12, 12]

            surface.blit(self.tex, (0, 0),
                         (0, ["green", "red"].index(self.color)*16, 16, 16))
        surface.set_colorkey((1, 1, 1))
        screen.complete.blit(surface, (self.x, self.y))

    def get_hit(self, x_dir=1):
        if abs(self.xv) > 0:
            self.xv = 0
        else:
            self.xv = sign(x_dir)*shell_speed


class Koopa(BasicAI):
    def __init__(self, x, y, color):
        BasicAI.__init__(self, x, y, xv=-1.0, yv=0.0)
        self.color = color
        self.tex = pygame.image.load("./Resources/Spritesheet/Koopa.png")
        self.collision_box = [self.x + 2, self.y + 2, 12, 12]
        self.alive = True
        self.falling = False

    def update(self):
        surface = pygame.Surface((16, 24))  # Koopa texture is slightly larger
        if self.falling:
            self.yv += gravity
            self.y += self.yv
            surface.blit(self.tex, (0, 0), ((4*frames/fps) % 2 * 16,
                                            24*["green", "red"].index(self.color), 16, 24))
            surface = pygame.transform.flip(surface, False, True)
        else:
            self.move()
            if self.color == "red":
                next_x = self.x + self.xv
                try:
                    next_tile = screen.level.data[self.y/16 + 1][int(self.x + (self.width if self.xv > 0 else 0))/16 + sign(self.xv)]
                    if not isinstance(next_tile, str) and not next_tile.collision:
                        if int(next_x)/16 != int(self.x + (self.width if self.xv > 0 else 0))/16:
                            self.xv *= -1
                except IndexError:
                    pass

            self.collision_box = [self.x + 2, self.y + 2, 12, 12]
            surface.blit(self.tex, (0, 0),
                         ((2*frames/fps % 2) * 16, 24*["green", "red"].index(self.color), 16, 24))

        surface = pygame.transform.flip(surface, self.xv > 0, False)
        surface.set_colorkey((1, 1, 1))
        screen.complete.blit(surface, (self.x, self.y - 8))  # correction for larger texture size

    def get_hit(self):
        self.alive = False
        screen.level.entities.append(Shell(self.x, self.y + 8, 1, self.color))  # correction for larger texture size
        screen.level.entities.remove(self)
        screen.popups.append(Popup(self.x, self.y - 16, 200 + mario.jumped_enemies*200))
        screen.ui.score += 200 + mario.jumped_enemies*200


class Flower(object):
    def __init__(self, x, y):
        self.x = x
        self.target_y = y
        self.y = y + 16
        self.width = 12
        self.height = 14
        self.tex = pygame.image.load("./Resources/Spritesheet/Flower.png")
        self.state = "appearing"

    def update(self):
        if self.state == "appearing":
            self.y -= 1
            if self.y == self.target_y:
                self.state = "normal"

        surface = pygame.Surface((16, 16))
        surface.blit(self.tex, (0, 0), ((4*frames/fps % 4) * 16, 0, 16, 16))
        surface.set_colorkey((1, 1, 1))
        screen.complete.blit(surface, (self.x, self.y))


class Tile(object):
    def __init__(self, x, y, val,  tile_width=16, tile_height=16,):
        self.x = self.initial_x = x
        self.y = self.initial_y = y
        self.yv = 0.0
        self.width = tile_width
        self.height = tile_height
        self.val = val
        self.state = "normal"
        self.collision = False
        self.breakable = False
        self.movable = False
        self.contains_coin = "coin" in self.val
        self.contains_item = "item" in self.val
        self.collision_box = [self.x, self.y, self.width, self.height]
        self.tex = pygame.Surface((self.width, self.height))
        self.tex.fill((1, 1, 1))
        self.tex.set_colorkey((1, 1, 1))

        if self.val == "Ground":
            self.tex.blit(Bricks, (0, 0),
                          (0, 0, 16, 16))
            self.collision = True
        elif self.val == "Hard brick":
            self.tex.blit(Bricks, (0, 0),
                          (0, 16, 16, 16))
            self.collision = True
        elif "Bottom brick" in self.val:
            self.tex.blit(Bricks, (0, 0),
                          (32, 0, 16, 16))
            self.collision = self.breakable = self.movable = True
        elif "Top brick" in self.val:
            self.tex.blit(Bricks, (0, 0),
                          (16, 0, 16, 16))
            self.collision = self.breakable = self.movable = True
        elif "Question" in self.val:
            if "used" not in self.val:
                self.tex.blit(Bricks, (0, 0),
                              (385, 0, 16, 16))
                self.movable = True
            else:
                self.tex.blit(Bricks, (0, 0),
                              (432, 0, 16, 16))
            self.tex.set_colorkey((255, 255, 255))
            self.collision = True
        elif "Pipe" in self.val:
            if "Shaft" in self.val:
                if "Connector" in self.val:
                    index = ["top", "bottom"].index(self.val.split(" ")[1])
                    self.tex.blit(PipeConnectors, (0, 0),
                                  (0, 16*index, 16, 16))
                else:
                    index = ["left", "right", "top", "bottom"].index(self.val.split(" ")[1])
                    self.tex.blit(PipeShafts, (0, 0),
                                  (16*index, 0, 16, 16))
            elif "End" in self.val:
                index = ["left", "right", "top", "bottom"].index(self.val.split(" ")[1])
                self.tex.blit(PipeEnds, (0, 0),
                              (16*index, 0, 16, 16))
            self.tex.set_colorkey((12, 12, 12))
            self.collision = True

    def get_hit(self):
        if self.state != "hit":
            if self.contains_coin:
                screen.moving_coins.append(MovingCoin(self.x, self.y))
                screen.ui.coins += 1
                self.contains_coin = False
            self.state = "hit"
            self.yv = -5.0

    def release_item(self):
        if self.contains_item:
            if mario.power == 0:
                screen.items.append(Mushroom(self.x, self.y - 16))
            else:
                screen.items.append(Flower(self.x, self.y - 16))
            self.contains_item = False
        elif self.contains_coin:
            screen.moving_coins.append(MovingCoin(self.x, self.y))
            self.contains_coin = False
            # pick up coin

    def break_block(self):
        screen.level.data[self.y/16][self.x/16] = ""
        for particles in range(random.randint(3, 4)):
            particle_tex = pygame.Surface((3, 3))
            particle_tex.blit(self.tex, (0, 0),
                              (random.randint(0, 13), random.randint(0, 13), 3, 3))
            screen.particles.append(Particle(self.x + random.randint(0, 16),
                                             self.y + random.randint(0, 16),
                                             random.choice([-1, 1])*random.randint(15, 20)/15.0,
                                             -random.randint(4, 8),
                                             particle_tex))

    def update(self):
        if self.state == "normal":
            pass
        elif self.state == "hit":
            self.yv += gravity
            self.y += self.yv
            if self.y >= self.initial_y:
                self.state = "normal"
                self.release_item()
                self.y = self.initial_y

        screen.complete.blit(self.tex, (self.x, self.y))


class Pipe(object):
    def __init__(self, x, y, frequency, vertical):
        self.x = x
        self.y = y
        self.frequency = frequency
        self.vertical = vertical
        if self.vertical:
            self.collision_box = [self.x + 6, self.y - 3, 20, 6]
        else:
            self.collision_box = [self.x - 3, self.y + 6, 6, 20]


class Level(object):
    def __init__(self, background, file_name):
        self.file_name = file_name
        with open("./Resources/Level/%s.txt" % file_name) as level_data:
            self.raw_data = level_data.readlines()
            self.height = len(self.raw_data) * 16
            self.width = max(len(y) * 16 for y in self.raw_data)
        self.data = []
        self.travel_pipes = []
        self.standing_coins = []
        self.entities = []
        for y in range(len(self.raw_data)):
            row = []
            for x in range(len(self.raw_data[y])):
                value = self.raw_data[y][x]
                tile_value = ""
                if value in "GX":
                    if value == "G":
                        tile_value = "Ground"
                    else:
                        tile_value = "Hard brick"
                elif value in "Bb":
                    if 0 <= y - 1 < len(self.data):
                        if self.raw_data[y - 1][x] in "Bb":
                            if value == "B":
                                tile_value = "Bottom brick coin"
                            else:
                                tile_value = "Bottom brick"
                        else:
                            if value == "B":
                                tile_value = "Top brick coin"
                            else:
                                tile_value = "Top brick"
                    else:
                        if value == "B":
                            tile_value = "Bottom brick coin"
                        else:
                            tile_value = "Bottom brick"
                elif value in "Qq":
                    if value == "Q":
                        tile_value = "Question item"
                    elif value == "q":
                        tile_value = "Question coin"
                elif value == "C":
                    self.standing_coins.append(StandingCoin(16*x, 16*y))
                elif value in "v>+":
                    if value == "v":
                        if self.raw_data[y][x - 1] in "+v":
                            tile_value = "PipeShaftVert right"
                        elif self.raw_data[y][x + 1] in "+v":
                            tile_value = "PipeShaftVert left"
                    elif value == ">":
                        if self.raw_data[y - 1][x] == ">":
                            tile_value = "PipeShaftHor bottom"
                        elif self.raw_data[y + 1][x] == ">":
                            tile_value = "PipeShaftHor top"
                    elif value == "+":
                        if self.raw_data[y - 1][x] == "+":
                            tile_value = "PipeShaftConnector bottom"
                        elif self.raw_data[y + 1][x] == "+":
                            tile_value = "PipeShaftConnector top"
                elif value in "01234 56789 P":            # n < 5 in, n >= 5 out, 0 > 5, 1 > 6 etc. P for non travel
                    if self.raw_data[y][x - 1] == value or self.raw_data[y][x + 1] == value:
                        tile_value = "PipeEndVert"
                        if self.raw_data[y][x - 1] == value:
                            tile_value += " right"
                        elif self.raw_data[y][x + 1] == value:
                            tile_value += " left"
                    elif self.raw_data[y - 1][x] == value or self.raw_data[y + 1][x] == value:
                        tile_value = "PipeEndHor"
                        if self.raw_data[y - 1][x] == value:
                            tile_value += " bottom"
                        elif self.raw_data[y + 1][x] == value:
                            tile_value += " top"
                    if value in "01234 56789":
                        if int(value) not in [pipe.frequency for pipe in self.travel_pipes]:
                            if self.raw_data[y][x + 1] == ">":
                                self.travel_pipes.append(Pipe(x*16, y*16, int(value), False))
                            elif self.raw_data[y + 1][x] == "v":
                                self.travel_pipes.append(Pipe(x*16, y*16, int(value), True))
                elif value == "g":
                    self.entities.append(Goomba(16*x, 16*y))
                elif value == "k":
                    self.entities.append(Koopa(16*x, 16*y, "green"))
                elif value == "K":
                    self.entities.append(Koopa(16*x, 16*y, "red"))

                if tile_value:
                    row.append(Tile(16*x, 16*y, tile_value))
                else:
                    row.append(tile_value)
            self.data.append(row)
        self.background = pygame.image.load(background)


class UI(object):
    def __init__(self):
        self.font = mario_font
        self.background = pygame.image.load("./Resources/Spritesheet/UI.png")
        self.score = self.prev_score = 0
        self.score_text = self.font.render((6 - len(str(self.score)))*"0" + str(self.score), True, white)
        self.coins = self.prev_coins = 0
        self.coins_text = self.font.render((2 - len(str(self.coins)))*"0" + str(self.coins), True, white)
        self.time = 500

        self.world = self.prev_world = "1"
        self.stage = self.prev_stage = "1"
        self.world_text = self.font.render(self.world, True, white)
        self.stage_text = self.font.render(self.stage, True, white)

    def update(self):
        if frames % (fps/2) == 0 and self.time > 0:
            self.time -= 1

        surface = pygame.Surface((width, height))

        surface.blit(self.background, (0, 0))

        if self.prev_score != self.score:
            self.score_text = self.font.render((6 - len(str(self.score)))*"0" + str(self.score), True, white)
            self.prev_score = self.score

        if self.prev_coins != self.coins:
            self.coins_text = self.font.render((2 - len(str(self.coins)))*"0" + str(self.coins), True, white)
            self.prev_coins = self.coins

        if self.world != self.prev_world:
            self.world_text = self.font.render(self.world, True, white)
            self.prev_world = self.world

        if self.stage != self.prev_stage:
            self.stage_text = self.font.render(screen.level.file_name[1], True, white)
            self.prev_stage = self.stage

        time_text = self.font.render((3 - len(str(self.time)))*"0" + str(self.time), True, white)
        surface.blit(time_text, (208, 13))
        surface.blit(self.score_text, (24, 13))
        surface.blit(self.coins_text, (104, 13))
        surface.blit(self.world_text, (152, 13))
        surface.blit(self.stage_text, (168, 13))

        surface.set_colorkey((0, 0, 0))

        screen.screen.blit(surface, (0, 0))


class Screen(object):
    def __init__(self, level):
        self.screen = pygame.display.set_mode((width, height), pygame.DOUBLEBUF)
        pygame.display.set_caption("MARIO")
        self.level = level
        self.ui = UI()
        self.complete = pygame.Surface((self.level.width, self.level.height))
        self.camera = Camera()
        self.particles = []
        self.moving_coins = []
        self.items = []
        self.popups = []

    def update(self):
        self.screen.fill(white)
        for x in range(0, self.level.width, self.level.background.get_width()):
            if self.level.width - x > self.level.background.get_width():
                self.complete.blit(self.level.background, (x, 0))
            else:
                self.complete.blit(self.level.background, (x, 0),
                                   (0, 0, self.level.width - x, self.level.background.get_height()))

        for coin in self.moving_coins:
            coin.update()
            if coin.y >= coin.initial_y:
                self.moving_coins.remove(coin)
                self.popups.append(Popup(coin.x, coin.y - 16, 200))
                self.ui.score += 200

        for item in self.items:
            item.update()
            if item.x + item.width < self.camera.x or 0 > item.y + item.height or item.y > height:
                self.items.remove(item)
            if collision([mario.x, mario.y, mario.width, mario.height], [item.x, item.y, item.width, item.height]):
                self.items.remove(item)
                if type(item) == Mushroom:
                    if mario.power == 0:
                        mario.power_up_animation(1)
                    self.popups.append(Popup(mario.x, mario.y - 16, 500))
                    self.ui.score += 500
                elif type(item) == Flower:
                    if mario.power in [0, 1]:
                        mario.power_up_animation(2)
                    self.popups.append(Popup(mario.x, mario.y - 16, 2000))
                    self.ui.score += 2000

        for coin in self.level.standing_coins:
            coin.update()

        for entity in self.level.entities:
            if entity.x < self.camera.x + width or type(entity) == Shell:
                entity.update()
                if not entity.falling:
                    for entity_check in self.level.entities:
                        if entity_check != entity:
                            if type(entity_check) == Shell and entity_check.xv != 0:
                                if collision(entity.collision_box, entity_check.collision_box):
                                    entity.yv = initial_falling_speed
                                    entity.falling = True

            if not entity.alive and ((type(entity) == Goomba and entity.corpse_frames <= 0) or type(entity) not in [Goomba, Koopa]):
                self.level.entities.remove(entity)

            if entity.y > height:
                if entity in self.level.entities:
                    self.level.entities.remove(entity)

        mario.update()

        for x in range(int(self.camera.x/16) - 2, int(self.camera.x/16) + width/16 + 2):
            for y in range(len(self.level.data)):
                if 0 <= y < len(self.level.data) and 0 <= x < len(self.level.data[0]):
                    if not isinstance(self.level.data[y][x], str):
                        self.level.data[y][x].update()

        for particle in self.particles:
            particle.update()
            if self.camera.x > particle.x or particle.x > self.camera.x + width or particle.y > height:
                self.particles.remove(particle)

        for popup in self.popups:
            popup.update()
            if popup.frames <= 0:
                self.popups.remove(popup)

        self.screen.blit(self.complete, (0, 0), (self.camera.x, 0, width, height))
        self.ui.update()
        pygame.display.update()


screen = Screen(Level("./Resources/Level/11.png", "11"))


class Fireball(object):
    def __init__(self, x, y, xv):
        self.x = x
        self.y = y
        self.xv = xv
        self.yv = 0.0
        self.width = 8
        self.height = 8
        self.collision_box = [self.x + 2, self.y + 2, 4, 4]
        self.tex = pygame.image.load("./Resources/Spritesheet/Fireball.png")

    def move(self):
        checklist = []
        for x in range(int(self.x)/16 - 1, int(self.x)/16 + 2):
            for y in range(int(self.y)/16 - 1, int(self.y)/16 + 2):
                if 0 <= y < len(screen.level.data) and 0 <= x < len(screen.level.data[y]):
                    if not isinstance(screen.level.data[y][x], str):
                        checklist.append(screen.level.data[y][x])

        self.yv += gravity
        next_y = self.y + self.yv

        if next_y < 0:
            self.y = 0
            self.yv = 0.0
        else:
            allow_movement = True
            for checking in checklist:
                if checking.collision:
                    if collision([self.x, next_y, self.width, self.height],
                                 checking.collision_box):
                        if checking.state == "hit":
                            self.yv = checking.yv
                            next_y = self.y + self.yv
                        else:
                            allow_movement = False
                            if self.y < checking.y:
                                self.y = checking.y - self.height
                                self.yv = -self.yv
                            else:
                                self.destroy()
                            break

            if allow_movement:
                self.y = next_y
                if any([collision([self.x, self.y, self.width, self.height], tile.collision_box) if tile.collision else False for tile in checklist]):
                    self.yv = -fireball_bounce_speed
            else:
                self.yv = -fireball_bounce_speed

        next_x = self.x + self.xv

        allow_movement = True
        for checking in checklist:
            if checking.collision:
                if collision([next_x, self.y, self.width, self.height],
                             checking.collision_box):
                    allow_movement = False
                    self.xv *= -1
                    break

        if allow_movement:
            self.x = next_x
        else:
            self.destroy()

    def destroy(self):
        if self in mario.fireballs:
            mario.fireballs.remove(self)

    def update(self):
        self.move()
        self.collision_box = [self.x + 2, self.y + 2, 4, 4]
        if self.x > screen.camera.x + width or self.x < screen.camera.x:
            self.destroy()
        else:
            for entity in screen.level.entities:
                if collision(self.collision_box, entity.collision_box):
                    if not entity.falling:
                        entity.yv = initial_falling_speed
                        entity.falling = True
                        self.destroy()
                        break

            surface = pygame.Surface((self.width, self.height))
            surface.blit(self.tex, (0, 0),
                         (((frames % (3*fps/8))/(fps/8)) * 8, 0, 8, 8))
            surface.set_colorkey((0, 0, 0))
            screen.complete.blit(surface, (self.x, self.y))


class Mario(object):
    def __init__(self):
        self.height = small_mario_height
        self.width = 12
        self.x = 3 * 16
        self.y = 13 * 16 - self.height      # floor y - self.height
        self.xv = 0.0
        self.yv = 0.0
        self.xa = 0.0
        self.ya = 0.0
        self.power = 0
        self.lives = 3
        self.sprinting = False
        self.standing = True
        self.crouching = False
        self.busy = False
        self.x_dir = 1
        self.sprite = {
            0: pygame.image.load("./Resources/Spritesheet/Mario_small.png"),
            1: pygame.image.load("./Resources/Spritesheet/Mario_large.png"),
            2: pygame.image.load("./Resources/Spritesheet/Mario_powered.png")
        }
        self.walk_order = [1, 2, 3, 2]
        self.frame = 0
        self.walk_frame = 0
        self.iframes = 0
        self.jumped_enemies = 0
        self.holding = None
        self.fireballs = []
        self.max_fireballs = 2

    def move(self):
        global space_pressed

        prev_y = self.y
        prev_x = self.x

        checklist = []
        for x in range(int(self.x)/16 - 2, int(self.x)/16 + 3):  # [int(self.x)/16, int(self.x)/16 - 1, int(self.x)/16 + 1]:  #
            for y in range(int(self.y)/16 - 6, int(self.y)/16 + 3):
                if 0 <= y < len(screen.level.data) and 0 <= x < len(screen.level.data[y]):
                    if not isinstance(screen.level.data[y][x], str):
                        checklist.append(screen.level.data[y][x])

        self.yv += gravity
        next_y = self.y + self.yv

        if next_y < 0:
            self.y = 0
            self.yv = 0.0
        else:
            allow_movement = True
            for checking in checklist:
                if checking.collision:
                    if collision([self.x, next_y, self.width, self.height],
                                 checking.collision_box):
                        allow_movement = False
                        if self.y < checking.y:
                            self.y = checking.y - self.height
                            self.standing = True
                            space_pressed = False
                            self.jumped_enemies = 0
                        else:
                            print checking.val
                            if checking.breakable:
                                if mario.power > 0:
                                    checking.break_block()

                            if checking.movable:
                                checking.get_hit()

                            if "Question" in checking.val and "used" not in checking.val:
                                screen.level.data[checking.y/16][checking.x/16] = \
                                    Tile(checking.x, checking.y, checking.val.replace("coin", "") + " used")
                                screen.level.data[checking.y/16][checking.x/16].get_hit()
                            self.y = checking.y + checking.height
                        self.yv = 0.0
                        break

            if allow_movement:
                self.y = next_y
                if any([collision([self.x, self.y, self.width, self.height], tile.collision_box) if tile.collision else False for tile in checklist]):
                    self.yv = 0.0
                    # while loop used to be here
                    self.standing = True
                    self.jumped_enemies = 0
                if self.y > height:
                    print "game over"
                    pygame.joystick.quit()
                    pygame.quit()
                    quit()
            else:
                self.yv = 0.0

        self.xv += self.xa - (sign(self.xv)*friction*math.sqrt(abs(self.xv)**1.5))/10
        if abs(self.xv) <= 0.25 and abs(self.xa) == 0:
            self.xv = 0
            self.walk_frame = 0

        next_x = self.x + self.xv

        allow_movement = True
        if next_x > screen.camera.x:
            for checking in checklist:
                if checking.collision:
                    if collision([next_x, self.y, self.width, self.height],
                                 checking.collision_box):
                        allow_movement = False
                        if self.x < checking.x:
                            self.x = checking.x - self.width
                        elif self.x > checking.x:
                            self.x = checking.x + checking.width
                        self.xv = 0
                        self.walk_frame = 0
                        break

            if allow_movement:
                self.x = next_x
            if self.x > screen.camera.x + width/2:
                screen.camera.x = self.x - width/2
        else:
            self.x = screen.camera.x

        for entity in screen.level.entities:
            if entity.alive and not entity.falling:
                if collision([self.x, self.y, self.width, self.height], entity.collision_box):
                    if not collision([self.x, prev_y, self.width, self.height], entity.collision_box):
                        if type(entity) == Shell:
                            entity.get_hit(entity.x - self.x)
                        else:
                            entity.get_hit()
                        self.yv = -7.0
                        self.jumped_enemies += 1
                    else:
                        if self.iframes == 0:
                            if not (type(entity) == Shell and entity.xv == 0):
                                self.get_hit()
                                self.iframes = 1.5*fps

        if self.iframes > 0:
            self.iframes -= 1

        # changing y used to be after changing x

        for coin in screen.level.standing_coins:
            if collision([self.x, self.y, self.width, self.height], coin.hit_box):
                screen.level.standing_coins.remove(coin)
                screen.ui.coins += 1
                screen.popups.append(Popup(self.x, self.y - 16, 100))
                screen.ui.score += 100

        for pipe in screen.level.travel_pipes:
            if collision([mario.x, mario.y, mario.width, mario.height],
                         pipe.collision_box):
                if (pipe.vertical and self.crouching) or (not pipe.vertical and mario.xa > 0):
                    for p in screen.level.travel_pipes:
                        if p.frequency == pipe.frequency + 5:
                            self.in_travel(pipe)
                            mario.x = p.x + 10
                            mario.y = p.y
                            screen.camera.x = mario.x - 48
                            self.out_travel(p)

        if frames % 2 == 0:
            self.frame = (self.frame + 1) % 60
            if self.frame % (7 - int(abs(self.xv))) == 0:
                self.walk_frame = (self.walk_frame + 1) % 4

    def in_travel(self, pipe):
        self.busy = True
        if pipe.vertical:
            self.x = pipe.x + 10  # in the middle of the pipe
            for frame in range(self.height):
                self.y += 1
                screen.update()
                clock.tick(fps)
        else:
            self.y = pipe.y + 32 - self.height  # touching the ground
            self.standing = True
            self.jumped_enemies = 0
            for frame in range(self.width):
                self.x += 1
                screen.update()
                clock.tick(fps)
        self.busy = False

    def out_travel(self, pipe):
        self.busy = True
        if pipe.vertical:
            for frame in range(self.height):
                self.y -= 1
                screen.update()
                clock.tick(fps)
        else:
            for frame in range(self.width):
                self.x -= 1
                screen.update()
                clock.tick(fps)
        self.busy = False

    def get_hit(self):
        if self.power > 0:
            self.power_down(0)
        else:
            print "killed"

    def crouch(self):
        self.crouching = True
        if self.power > 0:
            self.y += big_mario_height - small_mario_height

    def uncrouch(self):
        if mario.power > 0:
            self.y -= (big_mario_height - small_mario_height)
            self.height = big_mario_height
        self.crouching = False

    def power_down(self, new_power):
        was_crouching = self.crouching
        if was_crouching:
            self.uncrouch()
        if new_power == 0 and self.power > 0:
            self.y = self.y + self.height - small_mario_height
            pass
        self.power = new_power
        if was_crouching:
            self.crouch()

    def power_up(self, new_power):
        was_crouching = self.crouching
        if was_crouching:
            self.uncrouch()
        if self.power == 0 and new_power > 0:
            self.y = self.y + small_mario_height - big_mario_height
            self.power = new_power
        elif self.power == 1:
            self.power = new_power
        if was_crouching:
            self.crouch()

    def power_up_animation(self, new_power):
        if self.iframes % 2 == 1:
            self.iframes += 1
        self.busy = True
        current_power = int(self.power)
        for frame in range(fps/4):
            if (frame / 2) % 2 == 0:
                self.power_up(new_power)
            else:
                self.power_down(current_power)
            screen.update()
            clock.tick(fps)
        self.power_up(new_power)
        self.busy = False

    def update(self):
        if self.power == 0 or self.crouching:
            self.height = small_mario_height
        else:
            self.height = big_mario_height

        if not self.busy:
            self.move()

        for fireball in self.fireballs:
            fireball.update()

        if self.iframes == 0 or self.iframes % 2 == 0:
            mario_surface = pygame.Surface((16, 16 if self.power == 0 else 32))
            if self.crouching and self.power > 0:
                mario_surface.blit(self.sprite[self.power], (0, 0), (6*18, 0, 16, 32))
            elif abs(self.yv) > 0:
                mario_surface.blit(self.sprite[self.power], (0, 0), (5*18, 0, 16, 16 if self.power == 0 else 32))
            elif abs(self.xv) > 0:
                if sign(self.xv) != self.x_dir:
                    mario_surface.blit(self.sprite[self.power], (0, 0),
                                       (4*18, 0, 16, 16 if self.power == 0 else 32))
                else:
                    mario_surface.blit(self.sprite[self.power], (0, 0),
                                       (18*self.walk_order[self.walk_frame], 0, 16, 16 if self.power == 0 else 32))
            else:
                mario_surface.blit(self.sprite[self.power], (0, 0),
                                   (0, 0, 16, 16 if self.power == 0 else 32))

            mario_surface.set_colorkey((12, 12, 12))

            screen.complete.blit(pygame.transform.flip(mario_surface, self.x_dir == -1, False),
                                 (self.x - 2, self.y + self.height - mario_surface.get_height()))

            if self.holding is not None:
                shell_surface = pygame.Surface((16, 16))
                shell_surface.blit(mario.holding.tex, (0, 0),
                                   (0, ["green", "red"].index(self.holding.color)*16, 16, 16))
                shell_surface.set_colorkey((1, 1, 1))
                if self.x_dir == -1:
                    screen.complete.blit(shell_surface, (self.x - 8, self.y + self.height/2 - 8))
                else:
                    screen.complete.blit(shell_surface, (self.x + self.width - 8, self.y + self.height/2 - 8))

    def shoot_fireball(self):
        if self.power == 2 and len(self.fireballs) < self.max_fireballs and not self.crouching:
            self.fireballs.append(Fireball(self.x if self.x_dir == -1 else (self.x + self.width),
                                           self.y + self.height/2, self.x_dir*fireball_speed))

mario = Mario()

frames = 0

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.joystick.quit()
            pygame.quit()
            quit()

        # MOUSE AND KEYBOARD EVENTS

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                left_pressed = 2
                if right_pressed == 2:
                    right_pressed -= 1
            elif event.key == pygame.K_d:
                right_pressed = 2
                if left_pressed == 2:
                    left_pressed -= 1
            elif event.key == pygame.K_s:
                down_pressed = True
            elif event.key == pygame.K_SPACE:
                if mario.standing:
                    space_pressed = True
            elif event.key == pygame.K_LSHIFT:
                mario.sprinting = True
                mario.shoot_fireball()

            elif event.key == pygame.K_r:
                print mario.power

        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                left_pressed = 0
            elif event.key == pygame.K_d:
                right_pressed = 0
            elif event.key == pygame.K_s:
                down_pressed = False
            elif event.key == pygame.K_LSHIFT:
                mario.sprinting = False
            elif event.key == pygame.K_SPACE:
                space_pressed = False

        # JOYSTICK EVENTS

        elif event.type == pygame.JOYAXISMOTION:
            direction = int(round(event.value))
            if event.axis == 0:
                if direction == 1:
                    right_pressed = 2
                    if left_pressed == 2:
                        left_pressed -= 1
                elif direction == -1:
                    left_pressed = 2
                    if right_pressed == 2:
                        right_pressed -= 1
                elif direction == 0:
                    left_pressed = right_pressed = 0

            elif event.axis == 1:
                if direction == 1:
                    down_pressed = True
                else:
                    down_pressed = False

        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button in [2, 1]:
                space_pressed = True
            elif event.button in [4, 0]:
                mario.sprinting = True
                mario.shoot_fireball()

        elif event.type == pygame.JOYBUTTONUP:
            if event.button in [2, 1]:
                space_pressed = False
            elif event.button in [4, 0]:
                mario.sprinting = False

    # REST

    if not mario.crouching or mario.power == 0 or not mario.standing:
        if right_pressed > left_pressed:
            mario.x_dir = 1
            if not mario.standing:
                mario.xa = jumping_acceleration
            elif mario.sprinting:
                mario.xa = sprinting_acceleration
            else:
                mario.xa = walking_acceleration
        elif right_pressed < left_pressed:
            mario.x_dir = -1
            if not mario.standing:
                mario.xa = -jumping_acceleration
            elif mario.sprinting:
                mario.xa = -sprinting_acceleration
            else:
                mario.xa = -walking_acceleration
        else:
            mario.xa = 0
    else:
        mario.xa = 0

    if space_pressed:
        if mario.standing:
            mario.standing = False
            mario.yv = -9.0
        elif mario.yv < 0:
            mario.yv *= 1.1

    if down_pressed:
        if not mario.crouching:
            mario.crouch()
    elif mario.crouching:
        if allow_uncrouch():
            mario.uncrouch()

    if mario.sprinting:
        for entity in screen.level.entities:
            if type(entity) == Shell and entity.xv == 0 and mario.holding is None and\
                    collision(entity.collision_box, [mario.x, mario.y, mario.width, mario.height]):
                mario.holding = entity
                screen.level.entities.remove(entity)
                break

    if not mario.sprinting and mario.holding is not None:
        if mario.x_dir == 1:
            screen.level.entities.append(Shell(mario.x + mario.width,
                                               mario.y, mario.x_dir, mario.holding.color, xv=shell_speed))
        else:
            screen.level.entities.append(Shell(mario.x - mario.holding.width,
                                               mario.y, mario.x_dir, mario.holding.color, xv=-shell_speed))
        mario.holding = None

    frames = (frames + 1) % fps

    screen.update()
    """
    curr_time = time.time()  # now we have time after processing
    diff = curr_time - prev_time  # frame took this much time to process and render
    delay = max(1.0/float(fps) - diff, 0)  # if we finished early, wait the remaining time to desired fps, else wait 0 ms!
    # unfortunately, delay is always greater than target fps, so the game runs in approximately 30 fps
    time.sleep(delay)"""
    #print clock.get_fps()
    #clock.tick(fps)
    #prev_time = curr_time
