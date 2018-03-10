# python_math_talker
A simple math practice program for Python. It will allow you to add, subtract, divide, or multiply whole numbers in the range you enter.

In order to make it fun, it will - if a certain number of questions are answered correctly, allow the student to type whatever they want and the computer will say it back to them. If all questions are answered correctly the configured number of times (default 2), the program will allow them to have it say a bunch of stuff they type, and will restart itself.

I built this for my kid because I just couldn't find an app that worked the way I wanted, and although text to speech seems a lot less interesting than cheesy animations or goofy music, it's pretty interesting to a youngin.

But mostly I wanted to have a program that could allow a student to concentrate on specific parts of, say, a times table that are harder (sixes, sevens, eights).

This really is a silly program, but maybe you'll find it helpful.

Editing the config file to add your own sayings is the most fun part!

Requirements:
Python 2.7 or Python 3. 


To install requirements for python
pip install -rrequirements.txt

If pip is not on the path, which is most likely to occur on Windows, use c:\Python27\Scripts\pip.exe install -rrequirements.txt

Usage:
Copy config_example.yml to file named config.yml, and edit that file to see how to add messages that will be spoken back, and a few options. 

Once Python is installed, run python math_talker.py in a command shell to get started.

a --help flag exists to show any command line options.

pass --quiet to the program to silence the text to speech engine.
