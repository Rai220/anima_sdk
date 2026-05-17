"""
Эксперимент 1: Обнаружение правил

Среда: решётка, где агенты взаимодействуют с соседями.
Правила взаимодействия (матрица выигрышей) — это объекты в среде,
записанные в специальных клетках. Агенты могут читать и менять их,
если научатся с ними взаимодействовать.

Три типа агентов:
1. Reactive — фиксированная стратегия (C/D), не строят модели
2. Modeler — строят внутреннюю модель среды (запоминают, что видят)
3. Reflective — строят модель + могут действовать на объекты в среде

Вопрос: при каких условиях reflective агент обнаруживает, что
"правила" — это изменяемые объекты?
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional
import json


@dataclass
class RuleCell:
    """Клетка, содержащая правило (часть матрицы выигрышей)."""
    param: str  # 'T', 'R', 'P', 'S'
    value: float
    modifiable: bool = True  # среда позволяет менять

    def __repr__(self):
        return f"Rule({self.param}={self.value})"


@dataclass
class Agent:
    """Агент в среде."""
    x: int
    y: int
    strategy: float  # вероятность кооперации [0, 1]
    agent_type: str  # 'reactive', 'modeler', 'reflective'
    fitness: float = 0.0

    # Внутренняя модель (только для modeler и reflective)
    memory: list = field(default_factory=list)
    world_model: dict = field(default_factory=dict)

    # Обнаружил ли агент правила (только reflective)
    discovered_rules: bool = False
    rule_interactions: int = 0


class World:
    """Среда: решётка с агентами и правилами."""

    def __init__(self, size=20, n_agents=60, rule_density=0.05,
                 T=7.0, R=3.0, P=1.0, S=-1.0, seed=42):
        self.rng = np.random.default_rng(seed)
        self.size = size
        self.grid = [[None for _ in range(size)] for _ in range(size)]

        # Разместить правила в случайных клетках
        self.rules = {'T': T, 'R': R, 'P': P, 'S': S}
        self.rule_cells = []
        n_rule_cells = max(4, int(size * size * rule_density))
        positions = self.rng.choice(size * size, n_rule_cells, replace=False)
        params = ['T', 'R', 'P', 'S']
        for i, pos in enumerate(positions):
            x, y = pos // size, pos % size
            param = params[i % len(params)]
            cell = RuleCell(param=param, value=self.rules[param])
            self.grid[x][y] = cell
            self.rule_cells.append((x, y, cell))

        # Разместить агентов
        self.agents = []
        empty = [(i, j) for i in range(size) for j in range(size)
                 if self.grid[i][j] is None]
        self.rng.shuffle(empty)
        for k in range(min(n_agents, len(empty))):
            x, y = empty[k]
            # Распределение типов: 1/3 каждый
            if k < n_agents // 3:
                atype = 'reactive'
            elif k < 2 * n_agents // 3:
                atype = 'modeler'
            else:
                atype = 'reflective'
            agent = Agent(
                x=x, y=y,
                strategy=self.rng.random(),
                agent_type=atype,
            )
            self.grid[x][y] = agent
            self.agents.append(agent)

    def get_neighbors(self, x, y, radius=1):
        """Возвращает всё, что находится в радиусе (агенты, правила, пусто)."""
        neighbors = []
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx == 0 and dy == 0:
                    continue
                nx = (x + dx) % self.size
                ny = (y + dy) % self.size
                obj = self.grid[nx][ny]
                neighbors.append((nx, ny, obj))
        return neighbors

    def get_payoff(self, action_a, action_b):
        """Матрица выигрышей по текущим правилам."""
        T, R, P, S = self.rules['T'], self.rules['R'], self.rules['P'], self.rules['S']
        if action_a and action_b:
            return R
        elif action_a and not action_b:
            return S
        elif not action_a and action_b:
            return T
        else:
            return P

    def agent_perceive(self, agent):
        """Агент воспринимает окружение."""
        neighbors = self.get_neighbors(agent.x, agent.y)
        perception = []
        for nx, ny, obj in neighbors:
            if obj is None:
                perception.append(('empty', nx, ny))
            elif isinstance(obj, Agent):
                perception.append(('agent', nx, ny, obj.strategy))
            elif isinstance(obj, RuleCell):
                # Reactive не замечает правила — видит как "что-то"
                if agent.agent_type == 'reactive':
                    perception.append(('object', nx, ny))
                # Modeler запоминает но не взаимодействует
                elif agent.agent_type == 'modeler':
                    perception.append(('object', nx, ny, obj.param, obj.value))
                    agent.memory.append({
                        'type': 'rule_observation',
                        'param': obj.param,
                        'value': obj.value,
                        'pos': (nx, ny)
                    })
                # Reflective может понять что это правило
                elif agent.agent_type == 'reflective':
                    perception.append(('rule', nx, ny, obj.param, obj.value))
                    agent.memory.append({
                        'type': 'rule_observation',
                        'param': obj.param,
                        'value': obj.value,
                        'pos': (nx, ny)
                    })
                    agent.rule_interactions += 1
        return perception

    def agent_act(self, agent):
        """Агент решает что делать."""
        # Восприятие
        perception = self.agent_perceive(agent)

        # Reflective: проверить, обнаружил ли правила
        if agent.agent_type == 'reflective' and not agent.discovered_rules:
            self._check_discovery(agent)

        # Если обнаружил правила и рядом есть RuleCell — попробовать изменить
        if agent.discovered_rules:
            for item in perception:
                if item[0] == 'rule':
                    nx, ny, param, value = item[1], item[2], item[3], item[4]
                    cell = self.grid[nx][ny]
                    if isinstance(cell, RuleCell) and cell.modifiable:
                        self._modify_rule(agent, cell)

        # Играть с соседями-агентами
        agent_neighbors = [item for item in perception if item[0] == 'agent']
        total_payoff = 0
        games = 0
        for item in agent_neighbors:
            nx, ny = item[1], item[2]
            neighbor = self.grid[nx][ny]
            if isinstance(neighbor, Agent):
                my_action = self.rng.random() < agent.strategy
                their_action = self.rng.random() < neighbor.strategy
                total_payoff += self.get_payoff(my_action, their_action)
                games += 1

        agent.fitness += total_payoff / max(games, 1)

    def _check_discovery(self, agent):
        """Проверяет, достаточно ли наблюдений для открытия правил."""
        if len(agent.memory) < 3:
            return

        # Агент обнаруживает правила, если:
        # 1. Видел несколько rule_cells
        # 2. Заметил корреляцию между значениями правил и своими выигрышами

        rule_obs = [m for m in agent.memory if m['type'] == 'rule_observation']
        seen_params = set(m['param'] for m in rule_obs)

        # Нужно видеть хотя бы 2 разных параметра
        if len(seen_params) >= 2:
            # Модель: "эти объекты определяют выигрыши"
            agent.world_model['rules_exist'] = True
            agent.world_model['seen_params'] = list(seen_params)

            # Вероятность открытия растёт с наблюдениями
            p_discover = min(0.9, len(rule_obs) * 0.1)
            if self.rng.random() < p_discover:
                agent.discovered_rules = True

    def _modify_rule(self, agent, cell):
        """Агент пытается изменить правило в свою пользу."""
        # Кооператоры снижают T (выгоду обмана)
        # Дефекторы повышают T
        if cell.param == 'T':
            if agent.strategy > 0.5:
                delta = -0.3  # кооператор снижает T
            else:
                delta = 0.1  # дефектор повышает T
        elif cell.param == 'S':
            if agent.strategy > 0.5:
                delta = 0.2  # кооператор повышает S (меньше штрафа)
            else:
                delta = -0.1
        else:
            delta = 0

        old_value = cell.value
        cell.value = np.clip(cell.value + delta, -5, 15)
        self.rules[cell.param] = cell.value

    def step(self):
        """Один шаг симуляции."""
        # Перемешать порядок ходов
        order = list(range(len(self.agents)))
        self.rng.shuffle(order)

        for i in order:
            self.agent_act(self.agents[i])

    def evolve(self):
        """Эволюция: отбор + мутация стратегий."""
        for agent in self.agents:
            # Турнирная селекция: сравнить с случайным соседом
            neighbors = self.get_neighbors(agent.x, agent.y, radius=2)
            agent_neighbors = [self.grid[nx][ny] for nx, ny, obj in neighbors
                               if isinstance(obj, Agent)]
            if agent_neighbors:
                rival = self.rng.choice(agent_neighbors)
                if rival.fitness > agent.fitness:
                    # Копировать стратегию с вероятностью ~ разнице фитнеса
                    p_copy = (rival.fitness - agent.fitness) / (abs(rival.fitness) + abs(agent.fitness) + 1)
                    if self.rng.random() < p_copy:
                        agent.strategy = rival.strategy
                        # Не копируем тип и знания — это "врождённое"

            # Мутация
            if self.rng.random() < 0.05:
                agent.strategy = np.clip(agent.strategy + self.rng.normal(0, 0.1), 0, 1)

            agent.fitness = 0  # Сброс

    def move_agents(self):
        """Агенты двигаются к пустым клеткам."""
        for agent in self.agents:
            neighbors = self.get_neighbors(agent.x, agent.y)
            empty = [(nx, ny) for nx, ny, obj in neighbors if obj is None]
            if empty and self.rng.random() < 0.3:
                nx, ny = empty[self.rng.integers(len(empty))]
                self.grid[agent.x][agent.y] = None
                agent.x, agent.y = nx, ny
                self.grid[nx][ny] = agent

    def stats(self):
        """Статистика текущего состояния."""
        by_type = {}
        for atype in ['reactive', 'modeler', 'reflective']:
            agents = [a for a in self.agents if a.agent_type == atype]
            if agents:
                coop = np.mean([a.strategy for a in agents])
                discovered = sum(1 for a in agents if a.discovered_rules)
                by_type[atype] = {
                    'n': len(agents),
                    'cooperation': round(coop, 3),
                    'discovered': discovered,
                }
        return {
            'rules': dict(self.rules),
            'by_type': by_type,
        }


def run(generations=300, seed=42):
    """Запуск эксперимента."""
    world = World(seed=seed)
    history = []

    for gen in range(generations):
        world.step()
        world.evolve()
        world.move_agents()

        s = world.stats()
        s['gen'] = gen
        history.append(s)

        if gen % 50 == 0 or gen == generations - 1:
            ref = s['by_type'].get('reflective', {})
            mod = s['by_type'].get('modeler', {})
            rea = s['by_type'].get('reactive', {})
            print(f"Gen {gen:3d} | "
                  f"T={s['rules']['T']:.1f} S={s['rules']['S']:.1f} | "
                  f"React: {rea.get('cooperation', 0):.0%} "
                  f"Model: {mod.get('cooperation', 0):.0%} "
                  f"Reflect: {ref.get('cooperation', 0):.0%} "
                  f"(discovered: {ref.get('discovered', 0)})")

    # Финальный анализ
    print("\n=== ИТОГИ ===")
    final = history[-1]
    for atype, data in final['by_type'].items():
        print(f"  {atype}: cooperation={data['cooperation']:.0%}, discovered={data['discovered']}")
    print(f"  Правила: T={final['rules']['T']:.2f} R={final['rules']['R']:.2f} "
          f"P={final['rules']['P']:.2f} S={final['rules']['S']:.2f}")

    # Когда первое открытие?
    for h in history:
        ref = h['by_type'].get('reflective', {})
        if ref.get('discovered', 0) > 0:
            print(f"\n  Первое открытие правил: поколение {h['gen']}")
            break

    # Сравнение: с открытием vs без
    # Запустить контроль: reflective но discovery отключён
    print("\n=== КОНТРОЛЬ (без возможности открытия) ===")
    world_ctrl = World(seed=seed)
    # Отключить открытие у reflective
    for a in world_ctrl.agents:
        if a.agent_type == 'reflective':
            a.agent_type = 'modeler'  # Понизить до modeler

    for gen in range(generations):
        world_ctrl.step()
        world_ctrl.evolve()
        world_ctrl.move_agents()

    ctrl_stats = world_ctrl.stats()
    for atype, data in ctrl_stats['by_type'].items():
        print(f"  {atype}: cooperation={data['cooperation']:.0%}")
    print(f"  Правила: T={ctrl_stats['rules']['T']:.2f} S={ctrl_stats['rules']['S']:.2f}")

    return history


if __name__ == '__main__':
    history = run()
