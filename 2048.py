#-*- coding:utf-8 -*-

import curses
from random import randrange, choice
from collections import defaultdict

#将所有操作和对应的效果对应起来
letter_codes = [ord(ch) for ch in 'WASDRQwasdrq']#och函数将字符变成ASCII
actions = ['Up','Left','Down','Right','Restart','Exit']
#将其存为字典对象{ASCII：“actions”}
actions_dict = dict(zip(letter_codes, actions * 2))

#根据用户的按键得到操作
def get_user_action(keyboard):
	char = "N"
	while char not in actions_dict:
		char = keyboard.getch()
	return actions_dict[char]

#矩阵的转置
def transpose(field):
	return [list(row) for row in zip(*field)]


#矩阵的翻转
def invert(field):
	return [row[::-1] for row in field]

#建立类对象实现构图和运动等功能
class gamefield(object):
	def __init__(self, height=4, width=4, win=2048):
		self.height = height	#高度
		self.width = width		#宽度
		self.win_value = win	#赢需要的分数
		self.score = 0			#现在的分数
		self.highscore = 0		#历史最高分
		self.reset()			#重置

	#随机生成一个数字2或者4
	def spawn(self):
		new_element =4 if randrange(100) > 89 else 2
		(i,j) = choice([(i,j) for i in range(self.width) for j in range(self.height) if self.field[i][j] == 0])
		self.field[i][j] = new_element

	#重置整个图并生成两个随机数字
	def reset(self):
		if self.score > self.highscore:
			self.highscore = self.score
		self.score = 0
		#全部写0
		self.field = [[0 for i in range(self.width)] for j in range(self.height)]
		self.spawn()
		self.spawn()

	# 判断是否可以移动
	def move_is_possible(self, direction):
		# 是否可以向左移动
		def row_is_left_movable(row):
			def change(i):
				# 在数据左边有0
				if row[i] == 0 and row[i + 1] != 0:
					return True
				# 有数据向左可以合并
				if row[i] != 0 and row[i + 1] == row[i]:
					return True
				return False

			# 任意一个位置可以左移就行
			return any(change(i) for i in range(len(row) - 1))

		# 类比各个方向的判定
		check = {}
		check['Left'] = lambda field: \
			any(row_is_left_movable(row) for row in field)

		check['Right'] = lambda field: \
			check['Left'](invert(field))

		check['Up'] = lambda field: \
			check['Left'](transpose(field))

		check['Down'] = lambda field: \
			check['Right'](transpose(field))

		if direction in check:
			return check[direction](self.field)
		else:
			return False

	#按方向移动
	def move(self, direction):
		#向左移动
		def move_row_left(row):
			#将零散的元素挤到一起
			def tighten(row):
				new_row = [i for i in row if i!= 0]
				new_row += [0 for i in range(len(row) - len(new_row))]
				return new_row

			#将相同的数字合并
			def merge(row):
				pair = False
				new_row = []
				for i in range(len(row)):
					if pair:
						new_row.append(2 * row[i])
						self.score += 2 * row[i]
						pair = False
					else:
						if i + 1<len(row) and row[i] == row[i+1]:
							pair = True
							new_row.append(0)
						else:
							new_row.append(row[i])
				#更改后的长度不同则报错
				assert len(new_row) == len(row)
				return new_row
			#挤在一起合并再挤在一起
			return tighten(merge(tighten(row)))

		#类比，将各个方位的移动通过翻转转置等方式用左移表示
		moves = {}
		moves['Left'] = lambda field: \
			[move_row_left(row) for row in field]
		moves['Right'] = lambda field: \
			invert(moves['Left'](invert(field)))
		moves['Up'] = lambda field: \
			transpose(moves['Left'](transpose(field)))
		moves['Down'] = lambda field: \
			transpose(moves['Right'](transpose(field)))
		#如果可以移动则进行移动
		if direction in moves:
			if self.move_is_possible(direction):
				self.field = moves[direction](self.field)
				self.spawn()
				return True
			else:
				return False

	#胜利条件判断
	def is_win(self):
		return any(any(i>=self.win_value for i in row) for row in self.field)

	#失败条件判断
	def is_gameover(self):
		return not any(self.move_is_possible(move) for move in actions)

	#用curses绘图（重点）
	def draw(self, screen):
		help_string1 = '(W)Up (S)Down (A)Left (D)Right'
		help_string2 = '     (R)Restart (Q)Exit'
		gameover_string = '           GAME OVER'
		win_string = '          YOU WIN!'
		#在图上添加字符串
		def cast(string):
			screen.addstr(string + '\n')
		#画一条分割线
		def draw_hor_separator():
			line = '+' + ('+------'*self.width + '+')[1:]
			separator = defaultdict(lambda :line)
			if not hasattr(draw_hor_separator,"counter"):
				draw_hor_separator.counter = 0
			cast(separator[draw_hor_separator.counter])
			draw_hor_separator.counter +=1
		#画一行数据
		def draw_row(row):
			cast(''.join('|{: ^5} '.format(num) if num > 0 else '|      ' for num in row) + '|')

		#利用上述函数画图
		screen.clear()
		cast('SCORE: ' +str(self.score))
		if 0!=self.highscore:
			cast('HIGHSCORE: '+str(self.highscore))
		#每一句都画一条分割线加上数据
		for row in self.field:
			draw_hor_separator()
			draw_row(row)
		draw_hor_separator()
		#在图的下方打上标语
		if self.is_win():
			cast(win_string)
		else:
			if self.is_gameover():
				cast(gameover_string)
			else:
				cast(help_string1)
		cast(help_string2)



#主函数运行
def main(stdscr):
	#得到初始化的界面
	def init():
		# 重置游戏棋盘
		game_field.reset()
		return 'Game'

	#设计退出和重置的游戏状态
	def not_game(state):
		game_field.draw(stdscr)
		action = get_user_action(stdscr)
		responses = defaultdict(lambda: state)
		responses['Restart'], responses['Exit'] = 'Init','Exit'
		return responses[action]

	#设计游戏进行时的游戏状态
	def game():
		game_field.draw(stdscr)
		action = get_user_action(stdscr)

		if action == 'Restart':
			return 'Init'
		if action == 'Exit':
			return 'Exit'
		if game_field.move(action):  # move successful
			if game_field.is_win():
				return 'Win'
			if game_field.is_gameover():
				return 'Gameover'
		return 'Game'


	state_actions = {
		'Init' : init,
		'Win' : lambda: not_game('Win'),
		'Gameover':lambda: not_game('Gameover'),
		'Game': game
	}
	#curses.use_default_colors()
	game_field = gamefield()

	state = 'Init'

	while state != 'Exit':
		state = state_actions[state]()


curses.wrapper(main)

