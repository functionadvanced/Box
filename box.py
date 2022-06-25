import random
from collections import defaultdict
import pickle
import os
file_name = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data.pl')


class PuzzleGenerator:

    def __init__(self):
        with open(file_name, 'rb') as fb:
            print('load level data.')
            self.all_levels = pickle.load(fb)
            print("num of lvs: "+str(len(self.all_levels)))

    def randomXY(self):
        return (random.randrange(0, self.h), random.randrange(0, self.w))

    def generate(self, w, h, seed=0):
        self.w, self.h = w, h
        self.wall_pos = []
        self.box_pos = []
        self.floor_pos = []
        self.player_pos = (-1, -1)
        self.target_pos = []
        index = []
        for i in range(h):
            for j in range(w):
                index.append((i, j))
        random.seed(seed)
        random.shuffle(index)
        # num_box = random.randint(1, 2)
        # num_wall = random.randint(w*h//8, w*h//4)
        num_box = 1 # start with one box and no wall
        num_wall = 0
        # first, determine the player pos
        for i in range(num_box):
            self.box_pos.append(index[i])
        for i in range(num_wall):
            self.wall_pos.append(index[num_box + i])
        self.player_pos = index[num_box + num_wall]
        self.floor_pos = [item for item in index
                          if item not in self.wall_pos]
        random.shuffle(self.floor_pos)
        self.target_pos = self.floor_pos[:num_box]

    def try_add_tile(self):
        empty_places = [
            i for i in self.floor_pos
            if i not in self.box_pos
            and i not in self.target_pos
            and i != self.player_pos]
        possible_box_places = [
            i for i in self.floor_pos
            if i not in self.box_pos
            and i != self.player_pos
        ]
        possible_target_places = [
            i for i in self.floor_pos
            if i not in self.target_pos
        ]

        if random.randint(0, 40) < 40:  # add wall
            if len(empty_places) > 0:
                random.shuffle(empty_places)
                self.wall_pos.append(empty_places[0])
                self.floor_pos.remove(empty_places[0])
                return True
        else:  # add box and target pair
            if len(possible_box_places) > 0 and len(possible_target_places) > 0:
                random.shuffle(possible_box_places)
                random.shuffle(possible_target_places)
                self.box_pos.append(possible_box_places[0])
                self.target_pos.append(possible_target_places[0])
                return True
        return False

    def get_path(self, target):
        q = [self.player_pos]
        v = [self.player_pos]
        dx = [0, 0, 1, -1]
        dy = [1, -1, 0, 0]
        path = dict()
        while q:
            t = q.pop(0)
            for i in range(4):
                n = (t[0]+dx[i], t[1]+dy[i])
                if n in self.floor_pos \
                    and n not in self.box_pos \
                        and n not in v:
                    path[n] = t
                    if n == target:
                        return path
                    q.append(n)
                    v.append(n)
        return []

    def is_adjacent(self, f, t):
        return abs(f[0]-t[0]) + abs(f[1]-t[1]) == 1

    def try_push(self, t):
        if t in self.box_pos:
            if self.is_adjacent(self.player_pos, t):
                n = (t[0]*2-self.player_pos[0], t[1]*2-self.player_pos[1])
                if n in self.floor_pos and n not in self.box_pos:
                    self.box_pos.remove(t)
                    self.box_pos.append(n)
                    self.player_pos = t

    def reachable_box_side(self, p, b):
        # p: player position, a tuple
        # b: boxes position, list of tuple
        q = [p]
        visited = {p}
        dx = [0, 0, 1, -1]
        dy = [1, -1, 0, 0]
        r = []
        possible_side_pos = []
        for (i, j) in b:
            for k in range(4):
                possible_side_pos.append((i+dx[k], j+dy[k]))
        while q:
            t = q.pop(0)
            for i in range(4):
                new_p = (t[0]+dx[i], t[1]+dy[i])
                if new_p in self.floor_pos and new_p not in b:
                    if new_p not in visited:
                        q.append(new_p)
                        visited.add(new_p)
                        if new_p in possible_side_pos:
                            r.append(new_p)
        r.sort()
        return r

    def solve(self):
        self.box_pos.sort()
        r = self.reachable_box_side(self.player_pos, self.box_pos)
        BFS_queue = [(tuple(self.box_pos), tuple(r), 0,)]
        visited = {BFS_queue[-1][:-1]}
        dx = [0, 0, 1, -1]
        dy = [1, -1, 0, 0]
        game_over_pos = self.get_game_over_box_pos()
        while BFS_queue:
            b, p, s = BFS_queue.pop(0)
            if len(visited) > 1e3:
                return False
            for (x, y) in p:
                for k in range(4):
                    new_p = x + dx[k], y + dy[k]
                    if new_p in b:
                        new_b = (new_p[0] + dx[k], new_p[1] + dy[k])
                        if new_b in self.floor_pos \
                            and new_b not in b \
                                and new_b not in game_over_pos:
                            new_b_list = [
                                item for item in b if item != new_p] + [new_b]
                            new_b_list.sort()
                            r = self.reachable_box_side(new_p, new_b_list)
                            new_state = (tuple(new_b_list), tuple(r))
                            if new_state not in visited:
                                if set(new_b_list) == set(self.target_pos):
                                    self.complexity = len(visited)
                                    self.min_steps = s+1
                                    return True
                                visited.add(new_state)
                                BFS_queue.append(new_state+(s+1,))
        return False

    def get_game_over_box_pos(self):
        game_over_pos = []
        four_corners = [[0, 2], [0, 3], [1, 2], [1, 3]]
        dx = [0, 0, 1, -1]
        dy = [1, -1, 0, 0]
        for (i, j) in self.floor_pos:
            if (i, j) not in self.target_pos:
                flag = False
                for a1, a2 in four_corners:
                    t1 = (i+dx[a1], j+dy[a1])
                    t2 = (i+dx[a2], j+dy[a2])
                    if t1 not in self.floor_pos and t2 not in self.floor_pos:
                        flag = True
                        break
                if flag:
                    game_over_pos.append((i, j))
        return game_over_pos

    def loadLevel(self, level):
        level %= len(self.all_levels)
        t = self.all_levels[level]
        self.wall_pos, \
            self.floor_pos, \
            self.box_pos, \
            self.target_pos, \
            self.player_pos, \
            self.w, self.h = t[0].copy(), t[1].copy(
            ), t[2].copy(), t[3].copy(), t[4], t[5], t[6]

    def printResult(self):
        # print(self.r)
        for i in range(self.h):
            for j in range(self.w):
                # print(self.r[(i, j)], end='')
                if (i, j) in self.box_pos:
                    print('B', end='')
                elif (i, j) in self.wall_pos:
                    print('#', end='')
                elif (i, j) == self.player_pos:
                    print('S', end='')
                else:
                    print('.', end='')

                if (i, j) in self.target_pos:
                    print('T ', end='')
                else:
                    print('  ', end='')
            print('')
        print(self.complexity)
        print(self.min_steps)


if __name__ == "__main__":
    a = PuzzleGenerator()
    result = []
    for i in range(3000):
        a.generate(8, 8, i)
        print(i)
        if a.solve():
            counter = 0
            # print('h')
            while(True):
                w, f, b, t = a.wall_pos.copy(), a.floor_pos.copy(
                ), a.box_pos.copy(), a.target_pos.copy()
                if a.try_add_tile():
                    if a.solve():
                        continue
                a.wall_pos, a.floor_pos, a.box_pos, a.target_pos = w, f, b, t
                counter += 1
                # print(counter)
                if counter > 1000:
                    break
            if a.min_steps > 7 and a.complexity > 100:
                a.printResult()
                result.append((a.wall_pos.copy(), a.floor_pos.copy(
                ), a.box_pos.copy(), a.target_pos.copy(), a.player_pos, a.w, a.h))

    print(result)

    with open(file_name, 'wb') as fp:
        pickle.dump(result, fp)
