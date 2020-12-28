import random
import numpy as np
import pygame

SCREEN_SIZE = 800
BACKGROUND_COLOR = (20, ) * 3
BORDER_COLOR = (0, ) * 3
BORDER_WIDTH = 2
ORIENTATIONS = N, S, E, W = range(4)
TILE_COLORS = {
    N: (0, 114, 189),  # blue
    S: (119, 172, 48),  # green
    E: (162, 20, 47),  # red
    W: (237, 177, 32),  # yellow
    None: (200, ) * 3
}
TILE_STEPS = {
    N: np.array([-1, 0]),
    S: np.array([1, 0]),
    E: np.array([0, 1]),
    W: np.array([0, -1]),
}
TILE_STEP_CONFLICTS = {
    N: S,
    S: N,
    E: W,
    W: E,
}


class Domino:
    def __init__(self, upper_left_corner, orientation, order=None):
        assert orientation in ORIENTATIONS
        self.upper_left_corner = np.array(upper_left_corner)
        self.orientation = orientation
        self.rect = None

        if order is not None:
            self.gen_rect(order=order)

    def gen_rect(self, order):
        grid_size = SCREEN_SIZE / 2 / (order + 1)
        self.rect = pygame.Rect(
            round(grid_size * (order + 1 + self.upper_left_corner[1])),  # top
            round(grid_size * (order + 1 + self.upper_left_corner[0])),  # left
            round(grid_size * (2 if self.orientation in (N, S) else 1)),  # height
            round(grid_size * (1 if self.orientation in (N, S) else 2)),  # width
        )

    def step(self):
        self.upper_left_corner += TILE_STEPS[self.orientation]


class Diamond:
    def __init__(self, order, fps=4):
        assert type(order) is int and order > 0
        self.order = order
        self.fps = fps
        self.tiles = []

        self.diamond = None
        self.tiling = None
        self.generate_diamond_array()

        pygame.init()
        self.screen = pygame.display.set_mode([SCREEN_SIZE, SCREEN_SIZE])
        self.font = pygame.font.SysFont(pygame.font.get_default_font(), 32)
        self.clock = pygame.time.Clock()

        self.grid_rects = None
        self.generate_grid_rects()

    def generate_diamond_array(self):
        tri = np.triu(np.ones([self.order] * 2))
        self.diamond = np.concatenate([
            np.concatenate([np.flipud(tri), np.transpose(tri)], axis=1),
            np.concatenate([tri, np.fliplr(tri)], axis=1)
        ], axis=0)
        self.tiling = np.zeros([2 * self.order] * 2, dtype='O')

    def generate_grid_rects(self):
        self.grid_rects = [
            pygame.Rect(
                round(SCREEN_SIZE / 2 * (i + 1) / (self.order + 1)),  # left
                round(SCREEN_SIZE / 2 * (1 - (i + 1) / (self.order + 1))),  # top
                round(SCREEN_SIZE * (self.order - i) / (self.order + 1)),  # width
                round(SCREEN_SIZE * (i + 1) / (self.order + 1)),  # height
            )
            for i in range(self.order)
        ]

    def step_tile_generation(self, draw: bool = False):
        self.increase_order()
        if draw:
            self.draw()
        self.cancel_opposing_movers()
        if draw:
            self.draw()
        self.move_tiles()
        if draw:
            self.draw()
        self.fill_two_by_twos()
        if draw:
            self.draw()

    def increase_order(self):
        self.order += 1

        tiling = self.tiling
        self.generate_diamond_array()  # overwrites self.tiling
        self.tiling[1:-1, 1:-1] = tiling

        self.generate_grid_rects()
        [tile.gen_rect(order=self.order) for tile in self.tiles]

    def cancel_opposing_movers(self):
        for i, j in zip(*np.where(self.diamond)):
            tile = self.tiling[i, j]
            if tile == 0:
                continue
            i2, j2 = np.array([i, j]) + TILE_STEPS[tile.orientation]
            if not (0 <= i2 <= 2 * self.order and 0 <= j2 <= 2 * self.order):
                continue
            tile2 = self.tiling[i2, j2]
            if tile2 == 0:
                continue
            if tile2.orientation == TILE_STEP_CONFLICTS[tile.orientation]:
                self.tiling[np.where(self.tiling == tile)] = 0
                self.tiling[np.where(self.tiling == tile2)] = 0
                self.tiles.remove(tile)
                self.tiles.remove(tile2)

    def move_tiles(self):
        self.tiling = np.zeros([2 * self.order] * 2, dtype='O')
        for tile in self.tiles:
            tile.step()
            tile.gen_rect(order=self.order)
            self.tiling[tuple(tile.upper_left_corner + self.order)] = tile
            self.tiling[tuple(tile.upper_left_corner + self.order
                              + (TILE_STEPS[S] if tile.orientation in (E, W) else TILE_STEPS[E])
                              )] = tile

    def fill_two_by_twos(self):
        while np.any((self.tiling == 0) & (self.diamond == 1)):
            ii, jj = [i[0] for i in np.where((self.tiling == 0) & (self.diamond == 1))]
            if random.random() < 0.5:
                tile_a = Domino((ii - self.order, jj - self.order), W, self.order)
                self.tiling[ii, jj] = tile_a
                self.tiling[ii + 1, jj] = tile_a
                tile_b = Domino((ii - self.order, jj - self.order + 1), E, self.order)
                self.tiling[ii, jj + 1] = tile_b
                self.tiling[ii + 1, jj + 1] = tile_b
            else:
                tile_a = Domino((ii - self.order, jj - self.order), N, self.order)
                self.tiling[ii, jj] = tile_a
                self.tiling[ii, jj + 1] = tile_a
                tile_b = Domino((ii - self.order + 1, jj - self.order), S, self.order)
                self.tiling[ii + 1, jj] = tile_b
                self.tiling[ii + 1, jj + 1] = tile_b
            self.tiles.append(tile_a)
            self.tiles.append(tile_b)

    def draw(self):
        self.handle_events()
        self.blank_screen()
        self.draw_grid()
        self.draw_tiles()
        self.draw_annotations()
        pygame.display.flip()

    def handle_events(self):
        if self.fps is not None:
            self.clock.tick(self.fps)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

    def blank_screen(self):
        self.screen.fill(BACKGROUND_COLOR)

    def draw_grid(self):
        [
            pygame.draw.rect(self.screen, rect=rect, color=TILE_COLORS[None])
            for rect in self.grid_rects
        ]
        pygame.draw.line(
            self.screen,
            color=BORDER_COLOR,
            start_pos=(round(SCREEN_SIZE / 2 / (self.order + 1)), round(SCREEN_SIZE / 2)),
            end_pos=(round(SCREEN_SIZE / 2 * (1 + self.order / (self.order + 1))), round(SCREEN_SIZE / 2)),
            width=BORDER_WIDTH if self.order < 90 else 1
        )
        pygame.draw.line(
            self.screen,
            color=BORDER_COLOR,
            start_pos=(round(SCREEN_SIZE / 2), round(SCREEN_SIZE / 2 / (self.order + 1))),
            end_pos=(round(SCREEN_SIZE / 2), round(SCREEN_SIZE / 2 * (1 + self.order / (self.order + 1)))),
            width=BORDER_WIDTH if self.order < 90 else 1
        )
        [
            pygame.draw.rect(self.screen, rect=rect, color=BORDER_COLOR, width=BORDER_WIDTH if self.order < 90 else 1)
            for rect in self.grid_rects
        ]

    def draw_tiles(self):
        for tile in self.tiles:
            pygame.draw.rect(self.screen, rect=tile.rect, color=TILE_COLORS[tile.orientation])
            pygame.draw.rect(self.screen, rect=tile.rect,
                             color=BORDER_COLOR, width=BORDER_WIDTH if self.order < 90 else 1)

    def draw_annotations(self):
        label = self.font.render(f'A({self.order})', True, TILE_COLORS[None])
        self.screen.blit(label, np.array([SCREEN_SIZE, 0]).astype(int) + [-label.get_width(), 0])
