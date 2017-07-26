#!/usr/local/bin/python3
# coding: UTF-8
# Author: David
# Email: youchen.du@gmail.com
# Created: 2017-01-08 09:42
# Last modified: 2017-07-26 09:38
# Filename: CourseHelper.py
# Description:
import requests
import re
import json
import logging
import sys
import time

from logging import info
from datetime import datetime
from PIL import Image
from collections import namedtuple
from multiprocessing.dummy import Pool
from multiprocessing import Lock
from tempfile import TemporaryFile


__all__ = ['CourseHelper']

logging.basicConfig(
    stream=sys.stdout, level=logging.INFO,
    # format='%(asctime)s %(filename)s[line:%(lineno)d] %(message)s',
    format='%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')


enroll_infos = ['class_name', 'class_room', 'department', 'cno',
                'cname', 'teacher', 'interval', 'hour',
                'credit', 'max_people', 'max_status', 'enroll_method',
                'cur_method', 'more_info', 'action_id']
Enroll_Course = namedtuple('Enroll_Course', enroll_infos)

program_infos = ['cno', 'cname', 'plan', 'ctype', 'required',
                 'credit', 'hour', 'term', 'note']
Program_Course = namedtuple('Program_Course', program_infos)


def chinese(d):
    cnt = 0
    ed = bytes(d.encode('utf-8'))
    for c in ed:
        if c > 127:
            cnt += 1
    return cnt/3


def join(l):
    s = ''
    if isinstance(l, list):
        for elem in l:
            s += join(elem)
    else:
        s += ' '+str(l)
    return s


class MaxTryTimesException(Exception):
    pass


class CourseHelper:
    # fmts
    fmts = '{0[0]:{0[1]}}{1[0]:{1[1]}}{2[0]:{2[1]}}{3[0]:{3[1]}}'
    fmts += '{4[0]:{4[1]}}{5[0]:{5[1]}}{6[0]:{6[1]}}{7[0]:{7[1]}}'
    # Related URLs
    login_url = 'http://202.118.65.123/pyxx/login.aspx'
    captcha_url = 'http://202.118.65.123/pyxx/PageTemplate/NsoftPage/yzm/createyzm.aspx?'
    course_url = 'http://202.118.65.123:80/pyxx/pygl/pyjhxk.aspx?xh='
    program_url = 'http://202.118.65.123/pyxx/pygl/pyjhcx.aspx?xh='

    # Regular expressions
    field_value_pat = re.compile('<input.*?name="(.*?)".*?value="(.*?)".*?>')
    course_table_pat = re.compile('<table[\s\S]*?</table>')
    course_pat = re.compile('<tr[\s\S]*?>([\s\S]*?)</tr>')
    detail_pat = re.compile('<td[\s\S]*?>(.*?)</td>')
    course_id_pat = re.compile('__doPostBack\(&#39;(.*?)&#39;')
    week_pat = re.compile('([\d]+-[\d]+周)')
    day_pat = re.compile('(星期[一二三四五]) ([上午|下午|晚上]+)(\S+)')

    # Headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'}

    username = ''
    password = ''

    proxies = None
    pool = None

    __jobs = []
    __job_num = 0

    @staticmethod
    def get_now():
        now = datetime.now().strftime('%a %b %d %Y %H:%M:%SGMT+0800 (CST)')
        return now

    def __init__(self, username, password, *args, **kwargs):
        self.username = username
        self.password = password
        self.course_url += self.username
        self.program_url += self.username

        self.pool = Pool()
        self.lock = Lock()
        self.conn = requests.Session()
        self.conn.headers.update(self.headers)
        for key, value in kwargs.items():
            setattr(self, key, value)
        if self.proxies:
            self.conn.proxies.update(self.proxies)

        self._setup_cookie()
        self._login()
        self._process_student_program()
        self._process_courses_table()
        info('初始化完成...')

    def _check(self):
        if not self.username or not self.password:
            raise Exception('Wrong username or password')

    def _setup_cookie(self):
        payload = {}
        payload['ctl00$txtusername'] = self.username
        payload['ctl00$txtpassword'] = self.password
        payload['ctl00$txtyzm'] = ''
        resp = self.conn.get(self.login_url)
        payload.update(dict(self.field_value_pat.findall(resp.text)))
        self.payload = payload

    def _get_captcha(self):
        info('获取验证码中，请稍等...')
        resp = self.conn.get(self.captcha_url, params={'id': self.get_now()})
        info('等待用户输入验证码...')
        with TemporaryFile() as f:
            f.write(resp.content)
            f.seek(0)
            img = Image.open(f)
            img.show()
        payload = {}
        payload['ctl00$ImageButton1.x'] = img.size[0]
        payload['ctl00$ImageButton1.y'] = img.size[1]
        captcha = input('请输入验证码:')
        payload['ctl00$txtyzm'] = captcha
        self.payload.update(payload)

    def _login(self):
        info('正在尝试登录选课系统，请稍等...')
        while True:
            self._get_captcha()
            resp = self.conn.post(self.login_url, data=self.payload)
            if not resp.url.endswith('login.aspx'):
                break
            info('验证码错误，请重新输入')

    def _process_student_program(self):
        info('读取培养计划中，请稍等...')
        resp = self.conn.get(self.program_url)
        raw_html = resp.text

        table_html = self.course_table_pat.findall(raw_html)[1]
        table_html = table_html.replace('\r', '')
        table_html = table_html.replace('\n', '')
        table_html = table_html.replace('\t', '')

        labels = []
        courses = []
        for idx, course in enumerate(self.course_pat.findall(table_html)):
            data = self.detail_pat.findall(course)
            if idx == 0:
                labels = data
            else:
                data = [x.strip(' ') if x != '&nbsp;' else '' for x in data]
                pc = Program_Course(*data)
                courses.append(pc)
        labels = [re.sub(r'<.*?>', '', x) for x in labels]
        self.program_labels = labels
        self.program_courses = courses

    def _process_courses_table(self):
        info('读取课程信息中，请稍等...')
        resp = self.conn.get(self.course_url)
        raw_html = resp.text
        table_html = self.course_table_pat.findall(raw_html)[0]
        table_html = table_html.replace('\r', '')
        table_html = table_html.replace('\n', '')
        table_html = table_html.replace('\t', '')

        labels = []
        courses = []
        for idx, course in enumerate(self.course_pat.findall(table_html)):
            data = self.detail_pat.findall(course)
            if idx == 0:
                labels = data
            else:
                data = [x.strip(' ') if x != '&nbsp;' else '' for x in data]
                res = self.course_id_pat.findall(data[-1])
                if res:
                    data[-1] = res[0]
                else:
                    data[-1] = ''
                interval = data[6]
                weeks = self.week_pat.findall(interval)
                if weeks:
                    weeks = weeks[0]
                    days = self.day_pat.findall(interval)
                    days = [list(v) for v in days]
                    for v in days:
                        v[-1] = v[-1].split(',')
                        v[-1] = v[-1][0]+'-'+v[-1][-1]
                    data[6] = [weeks, days]
                course = Enroll_Course(*data)
                courses.append(course)
        self.enroll_courses = courses
        self.enroll_labels = labels

        payload = dict(self.field_value_pat.findall(raw_html))
        payload['ctl00%24MainWork%24dropKeyword'] = '1'
        payload['ctl00%24MainWork%24txtKeyword'] = ''
        payload['__ASYNCPOST'] = 'true'
        # payload['__EVENTTARGET'] = courses[1].action_id
        self.payload = payload

    def help_my_course(self, cname=''):
        """
            Interact and add to job list
        """
        if not cname:
            cname = input('输入课程名称(部分匹配): ')
        if not cname:
            return ''
        related_courses = list(filter(lambda x: cname in x.cname and x.teacher,
                                      self.enroll_courses))
        if not related_courses:
            return cname
        self._info_courses(related_courses)
        cno = int(input('请输入选课序号: '))
        idx = cno-1
        self._new_job(related_courses[idx])
        return cname

    def _info_courses(self, courses):
        labels = ['选课序号'] + self.enroll_labels[:7]
        labels = [[x, int(20-chinese(x))] for x in labels]
        labels[5][1] += 20
        labels[7][1] += 10
        info(self.fmts.format(*labels))
        for idx, course in enumerate(courses, 1):
            d = ['[{0}]'.format(idx)]+list(course[:7])
            d[-1] = join(d[-1]).strip(' ')
            d = [[x, int(20-chinese(x))] for x in d]
            d[5][1] += 20
            d[7][1] += 10
            info(self.fmts.format(*d))

    def _new_job(self, course):
        if course.action_id in self.__jobs:
            info('所选课程已存在')
            return
        if not course.action_id:
            info('课程无相关操作')
            return
        info('新选中课程: {0}'.format(str(course[:6])))
        self.__jobs.append(course)

    def _enroll_course(self, course, payload, max_times=5):
        if max_times == 0:
            raise MaxTryTimesException()
        try:
            resp = self.conn.post(self.course_url, data=payload)
            jd = resp.text[resp.text.find('{'):-1]
            reason = json.loads(jd)['text']
            code = 0
        except Exception as e:
            info(e)
            reason = '失败'
            code = -1
            self._try_enroll(course, max_times-1)
        finally:
            return (course.cname, reason, code)

    def _enroll_callback(self, result):
        info('<{0[0]}>处理结果: {0[1]} {0[2]}'.format(result))
        if result[2] == 0:
            self.lock.acquire()
            self.__job_num -= 1
            self.lock.release()

    def _enroll_errback(self, exception):
        info(exception)

    def _try_enroll(self, course, max_times):
        payload = self.payload.copy()
        payload['__EVENTTARGET'] = course.action_id
        self.pool.apply_async(self._enroll_course,
                              args=(course, payload, max_times),
                              callback=self._enroll_callback,
                              error_callback=self._enroll_errback)

    def start(self):
        info('启动选课过程')
        self._check()

        for course in self.__jobs:
            self.__job_num += 1
            info('处理中课程: {0}'.format(course.cname))
            self._try_enroll(course, max_times=5)

        while True:
            self.lock.acquire()
            flag = True if self.__job_num == 0 else False
            self.lock.release()
            if flag:
                break
            time.sleep(1)

        self.pool.close()
        self.pool.join()
