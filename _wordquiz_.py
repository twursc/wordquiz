#!/usr/bin/python
# -*- coding: utf-8 -*-  
# PyWordQuiz, using Python version 2.7
# Owner Wu, 2016/07/28

database_name = "cet4_160728.db"   # 数据库文件名
table_name = "CET-4"   # 词汇表名称
review_days = 3   # 隔多少天需要重新复习
quiz_availoptions = 4   # 每个问题提供多少个选项
sess_review_count = 20   # 每个会话提问多少个单词后开始复习，确定是否熟记
learn_time = 2   # 每个单词需要提问多少次可确定熟记
check_update = True   # 是否检查更新
current_version = 20
update_url = "https://raw.githubusercontent.com/twursc/wordquiz/master/latest_version_code"   # 更新检查地址

import sys
import time
import random
import sqlite3
import urllib2

print u" "
print u"  单词记忆测试 " + table_name
print u" --------------------------------------------------------------------------"

if check_update:
	update_info = urllib2.urlopen(update_url).read()
	if int(update_info) > current_version:
		print u"  发现新版本的 PyWordQuiz。"
		print u"  可以在 https://github.com/twursc/wordquiz 获取新版本。\n "

sys.stdout.write(u"  正在加载数据库... ")

current_time = int(time.time())
conn = sqlite3.connect(database_name)
curs = conn.execute("SELECT * From wordlist;")
db_words_count = 0
ack_count = 0
display_count = 0
all_words = []
display_words = []
bingo_words = []
time.sleep(0.1)
sess_asked_quiz = 0
sess_correct = 0
sess_corrupt = 0
sess_time_sum = 0

for row in curs: 
	db_words_count = db_words_count + 1
	all_words.append({"word": row[2], "translation": row[3], "bingo_times": 0})
	# if there're 3 days lack between the database time and current time, the word needs to be reviewed.
	if int(row[4] >= 1400000000):      # check if it's a valid timestamp
		if(current_time - int(row[4]) >= review_days * 86400):
			# need-to-review word
			display_words.append({"word": row[2], "translation": row[3], "bingo_times": 0})
			display_count = display_count + 1 
		else:
			ack_count = ack_count + 1
	else:
		display_words.append({"word": row[2], "translation": row[3], "bingo_times": 0})
		display_count = display_count + 1 

sys.stdout.write(str(db_words_count) + u" 个单词已加载。 \n")

if db_words_count - ack_count == 0:
	print u"  没有需要提问的单词。\n"
	sys.exit(0)

print u"  已确定 " + str(ack_count) + u" 个本次不需提问的单词。\n"

print u"  选择工作模式：1.提问单词，选翻译"
print u"                2.提问翻译，选单词"
work_mode = raw_input("  >>> ")
if work_mode == "1":
	var_ques = "word"
	var_option = "translation"
elif work_mode == "2":
	var_ques = "translation"
	var_option = "word"
else:
	print u"  输入的值无效。结束。"
	sys.exit(0)


print u"  "
print u"  提问过程中："
print u"      输入 s 可以显示本次提问的统计信息。"
print u"      输入 q 可以停止并将当前进度保存到数据库。"
print u"  "
print u"  按 [Enter] 开始提问。"
raw_input("")

def stopQuiz():
	#man_savedb()
	print "Terminated.\n"
	sys.exit(0)
def showStatistics():
	if sess_asked_quiz == 0:
		average_sec = 0
	else: average_sec = sess_time_sum / sess_asked_quiz

	print u" --------------------------------------------------------------------------"
	print u"  当前会话："
	print u"    已提问: " + str(sess_asked_quiz) + u" 个单词"
	print u"    回答错误次数：" + str(sess_corrupt)
	print u"    回答正确次数：" + str(sess_correct)
	print u"    平均答题时间：" + str(average_sec) + u" 秒"
	print u"  数据库中 " + str(review_days) + u" 天内 " + str(ack_count) + u" 个单词不需要再次提问"
	print u" --------------------------------------------------------------------------"
	raw_input(u"  Press [Enter] to continue.\n")


while True:
	display_count = len(display_words)
	if display_count == 0 and len(bingo_words) == 0:
		print u"  结束。没有更多的单词需要提问了。\n"
		break;

	if len(bingo_words) >= sess_review_count or len(display_words) == 0:
		# get words from bingoed words list
#		print "Random from Bingoed words, " + str(len(bingo_words)) + " left."
		word_num = random.randint(0, len(bingo_words) - 1);
		target_word = bingo_words[word_num]
		bingo_sign = "*"
		word_is_bingoed = True
	else:
#		print "Random from database words, " + str(len(display_words)) + " left."
		word_num = random.randint(0, display_count - 1);
		target_word = display_words[word_num]
		bingo_sign = " "
		word_is_bingoed = False
	print " " + bingo_sign + target_word[var_ques]
	
	quiz_options = {}
	quiz_count = 1
	correct_answer = random.randint(1, quiz_availoptions)
	quiz_options[correct_answer] = target_word[var_option]
	
	while True:    # Make a list of options
		if quiz_count != correct_answer:
			while True:
				translation_option_rand = random.randint(0, db_words_count - 1);
				if all_words[translation_option_rand][var_ques] != target_word[var_ques]:
					quiz_options[quiz_count] = all_words[translation_option_rand][var_option]
					break

		print "    (" + str(quiz_count) + ")" + quiz_options[quiz_count]
		quiz_count = quiz_count + 1
		if quiz_count > quiz_availoptions: break
	
	start_time = int(time.time())
	client_answer = raw_input("\r  >>> ")
	end_time = int(time.time())
	duration = end_time - start_time
	sess_time_sum = sess_time_sum + duration
	try:
		int_client_answer = int(client_answer)
	except:
		int_client_answer = -1
		# special command proceed
		if(client_answer) == "q":
			int_client_answer = 65536
			stopQuiz()
		elif(client_answer) == "s":
			int_client_answer = 65536
			showStatistics()
#		elif(client_answer) == "d":
#			int_client_answer = 65536
#			print display_words
#			print bingo_words
		
	if 1 <= int_client_answer <= quiz_availoptions:
		sess_asked_quiz = sess_asked_quiz + 1
		if int_client_answer == correct_answer:
			print u"\r  回答正确，耗时 " + str(duration) + u" 秒。"
			if word_is_bingoed:
#				print "Set '" + target_word["word"] + "' acknowledged."
				del bingo_words[word_num]
				ack_count = ack_count + 1
#				print "UPDATE wordlist Set acknowledged = " + str(int(time.time())) + " Where word = '" + target_word["word"] + "';"
				write_db = conn.execute("UPDATE wordlist Set acknowledged = " + str(int(time.time())) + " Where word = '" + target_word["word"] + "';")
				conn.commit()
			else:
				sess_correct = sess_correct + 1
#				print "Set '" + target_word["word"] + "' bingo."
				display_words[word_num]["bingo_times"] = display_words[word_num]["bingo_times"] + 1
				if display_words[word_num]["bingo_times"] >= learn_time - 1:
					bingo_words.append(display_words[word_num])
					del display_words[word_num]
		else:
			sess_corrupt = sess_corrupt + 1
			print u"\r  回答错误，耗时 " + str(duration) + u" 秒。正确选项是 (" + str(correct_answer) + ")" + quiz_options[correct_answer]
	else:
		if int_client_answer != 65536:
			print u"\r  输入的值无效。"


	print u"  "

#	raw_input();

