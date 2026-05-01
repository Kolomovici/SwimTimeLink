朋友们非常抱歉，因为"中国大学生游泳锦标赛 总决赛"的缘故,该项目开发团队无法到场支持湖南大学游泳校联赛，但是我们依然坚持将此项目开发完成！
感谢NJAU(南京农业大学)前端的支持！期待与您们在中国大学生游泳锦标赛————鄂尔多斯相见！

#Still under development!
![169bf32a324d35644874aba760ec36a9_720](https://github.com/user-attachments/assets/e6684343-0612-425f-9cb4-7b8ba412de89)

This project aims to provide simple timing without an electronic timing board
Please run this in 'python3.10'

*First change the paths in config.

*Put your WAV files in a folder, also change the paths in ESP.py

Then run ./ESP.py (press'4',start the game;press '5' test the time relay)

cd D:\CS\SwimTimeLink

# 运行全部测试（shared_functions + excel_writer）
python test_main.py

# 只测 shared_functions
python test_main.py --module=sf

# 只测 excel_writer
python test_main.py --module=ex

# 只测 API（需先启动 Flask 服务器）
python test_main.py --module=api

GenShin niubi
