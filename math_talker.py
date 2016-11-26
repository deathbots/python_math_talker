from __future__ import print_function, division

import numbers
import random
import operator
import time
import yaml
import os
import argparse
import six

if six.PY2:
    import pyttsx

# FIX raw input not avail in py3
try:
    input = raw_input
except NameError:
    pass

THIS_DIR = os.path.dirname(__file__)
CONF_PATH = os.path.join(THIS_DIR, 'config.yml')
NAME = 'unknown person'
CONF = None
quiet_mode = False
chosen_probs_list = []


# what you should do is calculate the multiplication, and then reverse numbers.
# check result against the div.
# allow the rate to be slowed down and then re-increased


def is_probably_true(chance_percentage):
    # given a percentage, has that probability to return True
    if random.randrange(100) >= chance_percentage:
        return False
    else:
        return True


def say(message, chance_percentage=100, one_time_rate=None):
    # todo: refactor this logical mess. Last minute rush to get py3 to work, which forced quiet mode
    global quiet_mode
    if chance_percentage != 100:
        if not is_probably_true(chance_percentage):
            return
    if one_time_rate is not None:
        if not quiet_mode:
            engine.setProperty('rate', one_time_rate)
    if quiet_mode:
        print(message)
        time.sleep(2)
    else:
        engine.say(message)
        engine.runAndWait()
        engine.setProperty('rate', CONF.speech_settings['rate'])


class Config(object):
    # load config from disk, ask for name, substitute name in any string in yaml string list
    # that contains $NAME.
    # engine is pyttsx.engine init result
    def __init__(self, config_path, engine, quiet_mode=False):
        self.required_config_sections = ['speech', 'reward', 'tries']
        self.required_string_sections = ['greetingMessages', 'successMessages', 'failureMessages', 'victoryMessages']
        self.all_required_sections = []
        self.all_required_sections.extend(self.required_config_sections)
        self.all_required_sections.extend(self.required_string_sections)
        self.raw_dict = None
        self._load_config(config_path)
        self.quiet_mode = quiet_mode
        self.name = None
        self.speech_settings = self.raw_dict['speech']
        self.reward_settings = self.raw_dict['reward']
        self.tries_settings = self.raw_dict['tries']
        self.reward_message = self.reward_settings['rewardMessage']
        self.free_speech_reward_count = self.reward_settings['speechCount']
        if not quiet_mode:
            engine.setProperty('rate', self.speech_settings.get('rate', 160))
        self.get_name()

    def _load_config(self, config_path):
        with open(config_path, 'r') as f:
            c = yaml.safe_load(f)
            for sec in self.all_required_sections:
                if not c[sec]:
                    raise RuntimeError('Config must have {}: section'.format(sec))
            self.raw_dict = c

    def get_name(self):
        if not quiet_mode:
            engine.say("{} What is your name?".format(self.random_greeting))
            engine.runAndWait()
        while not self.name:
            self.name = str(input("Type your name and press Enter:").strip(' \t\n\r'))
            if not self.name:
                print("You have to have a NAME, jeez. Try again.")
        self._nameify()
        if not quiet_mode:
            engine.say("OK let's do this {}".format(self.name))
            engine.runAndWait()

    def _nameify(self):
        for sec in self.required_string_sections:
            for i, v in enumerate(self.raw_dict[sec]):
                self.raw_dict[sec][i] = v.replace('$NAME', self.name)

    @property
    def greeting_strings(self):
        return self.raw_dict['greetingMessages']

    @property
    def success_strings(self):
        return self.raw_dict['successMessages']

    @property
    def tries_before_giving_answer(self):
        return self.tries_settings.get('tryUntilCertainTimes', 2)

    @property
    def tries_before_never_reasking(self):
        return self.tries_settings.get('tryAgainTimes', 2)

    @property
    def correct_answers_for_break(self):
        return self.reward_settings.get('rewardIfCorrect', 15)

    @property
    def failure_strings(self):
        return self.raw_dict['failureMessages']

    @property
    def victory_strings(self):
        return self.raw_dict['victoryMessages']

    @property
    def random_greeting(self):
        return random.choice(self.greeting_strings)

    @property
    def random_success(self):
        return random.choice(self.success_strings)

    @property
    def random_failure(self):
        return random.choice(self.failure_strings)

    @property
    def random_victory(self):
        return random.choice(self.victory_strings)


def old_div(a, b):
    """
    The old_div function from future.past.utils.
    http://python-future.org/index.html

    Equivalent to ``a / b`` on Python 2 without ``from __future__ import
    division``.

    TODO: generalize this to other objects (like arrays etc.)
    """
    if isinstance(a, numbers.Integral) and isinstance(b, numbers.Integral):
        return a // b
    else:
        return a / b


class ProbType(object):
    def __init__(self, operation):
        self._valid_ops = {'div': ['/', 'divided by', old_div],
                           'mul': ['X', 'times', operator.mul],
                           'add': ['+', 'plus', operator.add],
                           'sub': ['-', 'minus', operator.sub]
                           }
        self._operation = self._validate_operation(operation)
        self.op_name = operation

    def _validate_operation(self, op):
        if op not in self._valid_ops.keys():
            m = 'Invalid operation type {}, valid operations are: {}'
            raise RuntimeError(m.format(op, ' '.join(self._valid_ops)))
        return op

    @property
    def operation(self):
        return self._operation

    @operation.setter
    def operation(self, value):
        self._operation = self._validate_operation(value)

    @property
    def printable_name(self):
        return self._valid_ops[self._operation][1]

    @property
    def operator_symbol(self):
        return self._valid_ops[self._operation][0]

    def calc(self, a, b):
        return self._valid_ops[self._operation][2](a, b)

    def print_problem(self, one, two):
        print("   {0}".format(one))
        print("{0}  {1}".format(self.operator_symbol, two))
        print("------")

    def ask_problem(self, one, two):
        # returns True or False if answer is correct
        answer = self.calc(one, two)
        in_num = None
        while in_num is None:
            self.print_problem(one, two)
            try:
                in_num = int(input(": ").strip(' \t\n\r'))
            except Exception as e:
                print("..uhh try entering that again. Type a number and hit enter.")
        return answer == in_num

    def say_problem(self, one, two, times=1):
        for _ in range(times):
            say("{0} {1} {2} is {3}".format(one, self.printable_name, two, self.calc(one, two)))


def get_in_range(low, high):
    if low == high:
        return low
    return random.randrange(low, high)


def get_range():
    say("I know how to do addition, subtraction, multiplication, and division. "
        "This stuff will help you later in life.")
    try:
        min = int(input("Enter lowest number in table. Hit Enter for 2: ").strip(' \t\n\r') or "2")
    except ValueError:
        min = 2
    try:
        max = int(input("Enter highest number in table. Hit Enter for 9: ").strip(' \t\n\r') or "9")
    except ValueError:
        max = 9
    if max < min:
        max = min
    try:
        restrict_number = int(input("Enter a number you want to concentrate on. Hit "
                                    "enter for all : ").strip(' \t\n\r') or "-1")
    except ValueError:
        restrict_number = -1
    prob_type = str(input("Enter a for addition, s for subtraction, m for multiplication, d for division. "
                          "Or just hit Enter to do all types: ").strip(' \t\n\r') or "l").lower()

    return min, max, restrict_number, prob_type


def get_random_string(input_dict):
    return random.choice(input_dict.keys())


def substring_after(s, delim):
    # This is nice as it will return empty string if the delim doesn't appear.
    return s.partition(delim)[2]


def free_speech_mode(one_saying_mode=False):
    if quiet_mode:
        return
    sayings_allowed = CONF.free_speech_reward_count
    if not one_saying_mode:
        say(CONF.reward_message)
    else:
        sayings_allowed = 1
        say("You're doing so well, I'm going to let you tell me to say ONE THING.")

    print("Hint - if you want to, but you don't have to, you can type :30 at the end of the words you want me to "
          "say to make me say it at speed 30. "
          "290 is fast, 30 is extremely slow. For example, you could type \"hey there:200\"")
    for _ in range(sayings_allowed):
        try:
            m = str(input("What do you want me to say? I will do this {} more times. "
                          "Type anything and hit Enter:".format(sayings_allowed)).strip(' \t\n\r'))
        except:
            print("I wasn't able to figure that out. Try again?")
            sayings_allowed += 1
        else:
            rate_str = substring_after(m, ':')
            try:
                rate = int(rate_str)
                m = m.replace(':' + rate_str, '')
            except ValueError:
                rate = CONF.speech_settings['rate']
            try:
                say(m, one_time_rate=rate)
            except:
                print("Maybe {} was just not a good number. Try something between 30 and 200".format(rate))
                sayings_allowed += 1


def run_and_loop(min, max, restrict, prob_type):
    probs_dict = {'a': ProbType('add'),
                  's': ProbType('sub'),
                  'm': ProbType('mul'),
                  'd': ProbType('div')
                  }
    correct_count = 0
    good_answers = dict()
    skip_count = 0
    won_spoken = False
    if prob_type == 's':
        max += max  # Go to 20, for instance, for subtraction.
    while True:
        if correct_count > 0 and correct_count % CONF.correct_answers_for_break == 0:
            free_speech_mode(one_saying_mode=True)
        prob = probs_dict.get(prob_type, random.choice(list(six.itervalues(probs_dict))))
        one = get_in_range(min, max)
        two = get_in_range(min, max)
        if restrict != -1:
            two = restrict
        # here, if we are dividing, reverse things
        if prob.operation == 'div':
            one = two * one
        # if it's subtraction, don't do negative numbers
        if prob.operation == 'sub':
            if one < two:
                one, two = two, one
        key_f = "{0} {1}".format(one, two)
        answer_count_f = good_answers.get(key_f, 0)
        key_b = "{0} {1}".format(two, one)
        answer_count_b = good_answers.get(key_b, 0)
        if answer_count_f >= CONF.tries_before_never_reasking or answer_count_b >= CONF.tries_before_never_reasking:
            # skip answers they already know
            skip_count += 1
            if skip_count >= max * min:
                if not won_spoken:
                    say(CONF.random_victory, one_time_rate=100)
                    won_spoken = True
                print("{} YOU WON MATH, YOU GOT EACH POSSIBLE NUMBER "
                      "CORRECT {} TIMES".format(CONF.name, CONF.tries_before_never_reasking))
                free_speech_mode()
                print("Thank you for playing")
                return
            else:
                print("I was going to ask about {0} {1} {2} but you already knew that one, "
                      "picking another!".format(one, prob.printable_name, two))
            continue

        try_again_count = 0
        correct = prob.ask_problem(one, two)
        while True:
            if try_again_count == CONF.tries_before_giving_answer:
                print("-----remember this one, {}-----\n".format(CONF.name))
                prob.print_problem(one, two)
                print("   {0}".format(prob.calc(one, two)))
                print("-----------------------")
                say(CONF.random_failure)
                prob.say_problem(one, two, times=3)
                break
            if correct:
                correct_count += 1
                print("Correct! {0} {1} {2} is {3}.".format(one, prob.printable_name, two,
                                                            prob.calc(one, two)))
                if quiet_mode:  # looks strange to do this here, but otherwise it would print it twice
                    time.sleep(1)
                else:
                    prob.say_problem(one, two)
                say(CONF.random_success, 30)
                _ = os.system("cls")
                answer_count_f += 1
                good_answers[key_f] = answer_count_f
                answer_count_b += 1
                good_answers[key_b] = answer_count_b
                break
            else:
                print("Try again! You have {0} more tries"
                      .format(CONF.tries_before_giving_answer - try_again_count - 1))
                try_again_count += 1
                correct = prob.ask_problem(one, two)


def parse_args():
    parser = argparse.ArgumentParser(description='A talking math game.')
    parser.add_argument('--quiet', dest='quiet_flag', action='store_true')
    parser.set_defaults(quiet_flag=False)

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    quiet_mode = args.quiet_flag
    if quiet_mode:
        print('Quiet mode enabled. No talking!')
    engine = None
    if six.PY3:
        if not quiet_mode:
            print("I am sorry, but the text to speech engine will not work in Python 3. Try Python2.7 instead.")
            quiet_mode = True
    if not quiet_mode:
        engine = pyttsx.init()
        engine.setProperty('voice', "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_ZIRA_11.0")
    try:
        CONF = Config(CONF_PATH, engine, quiet_mode)
    except yaml.YAMLError as e:
        print("Could not load config file at {}, {}".format(CONF_PATH, str(e)))
    except RuntimeError as e:
        print("Config file at {} was not properly formatted, {}".format(CONF_PATH, str(e)))
    except (OSError, IOError) as e:
        print("Config file at {} was not found, {}".format(CONF_PATH, str(e)))
        print("Did you forget to copy config_example.yml to config.yml?")
    while True:
        min, max, restrict, prob_type = get_range()
        run_and_loop(min, max, restrict, prob_type)
