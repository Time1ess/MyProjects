import json

import scrapy
from scrapy.http import Request

from Zhihu.utils import replace_html_tag
from Zhihu.items import UserProfile, FollowRelationShip


class PeopleSpider(scrapy.Spider):
    name = 'people'
    allowed_domains = ['zhihu.com']
    people_url = 'https://www.zhihu.com/people/{}'
    followings_url = ('https://www.zhihu.com/api/v4/members/'
                      '{user}/followees?offset={offset}&limit=20')
    followers_url = ('https://www.zhihu.com/api/v4/members/'
                     '{user}/followers?offset={offset}&limit=20')
    headers = {'authorization': 'oauth c3cef7c66a1843f8b3a9e6a1e3160e20'}

    # data dict keys
    main_key = 'urlToken'
    loc_key = 'locations'
    emp_key = 'employments'
    edu_key = 'educations'
    voteup_key = 'voteUpCount'
    thanked_key = 'thankedCount'
    favorited_key = 'favoritedCount'
    answer_key = 'answerCount'
    question_key = 'questionCount'
    articles_key = 'articlesCount'
    columns_key = 'columnsCount'
    pins_key = 'pinsCount'
    favorite_key = 'favoriteCount'
    hosted_live_key = 'hostedLiveCount'
    participated_live_key = 'participatedLiveCount'
    following_topic_key = 'followingTopicCount'
    following_columns_key = 'followingColumnsCount'
    following_question_key = 'followingQuestionCount'
    following_fav_list_key = 'followingFavlistsCount'
    follower_key = 'followerCount'
    following_key = 'followingCount'

    def start_requests(self):
        root_token = 'excited-vczh'
        req = Request(self.people_url.format(root_token), callback=self.parse,
                      priority=10)
        return [req]

    def _parse_profile(self, data, item):
        name = data['name']
        headline = replace_html_tag(data['headline'])
        gender = data['gender']
        locations = [x['name'] for x in data[self.loc_key]]
        business = data['business']['name'] if 'business' in data else ''
        employments = []
        for employment in data[self.emp_key]:
            company = ''
            if 'company' in employment:
                company = employment['company']['name']
            job = ''
            if 'job' in employment:
                job = employment['job']['name']
            employments.append('{}-{}'.format(company, job))
        educations = []
        for edu in data[self.edu_key]:
            school = ''
            if 'school' in edu:
                school = edu['school']['name']
            major = ''
            if 'major' in edu:
                major = edu['major']['name']
            educations.append('{}-{}'.format(school, major))
        description = replace_html_tag(data['description'])

        item['name'] = name
        item['headline'] = headline
        item['gender'] = gender
        item['locations'] = locations
        item['business'] = business
        item['employments'] = employments
        item['educations'] = educations
        item['description'] = description

    def _parse_achievements(self, data, item):
        voteup_cnt = data[self.voteup_key]
        thanked_cnt = data[self.thanked_key]
        favorited_cnt = data[self.favorited_key]

        item['voteup_cnt'] = voteup_cnt
        item['thanked_cnt'] = thanked_cnt
        item['favorited_cnt'] = favorited_cnt

    def _parse_activities(self, data, item):
        answer_cnt = data[self.answer_key]
        question_cnt = data[self.question_key]
        article_cnt = data[self.articles_key]
        column_cnt = data[self.columns_key]
        pin_cnt = data[self.pins_key]
        favorite_cnt = data[self.favorite_key]
        hosted_live_cnt = data[self.hosted_live_key]
        participated_live_cnt = data[self.participated_live_key]
        following_topic_cnt = data[self.following_topic_key]
        following_column_cnt = data[self.following_columns_key]
        following_question_cnt = data[self.following_question_key]
        following_fav_list_cnt = data[self.following_fav_list_key]

        item['answer_cnt'] = answer_cnt
        item['question_cnt'] = question_cnt
        item['article_cnt'] = article_cnt
        item['column_cnt'] = column_cnt
        item['pin_cnt'] = pin_cnt
        item['favorite_cnt'] = favorite_cnt
        item['hosted_live_cnt'] = hosted_live_cnt
        item['participated_live_cnt'] = participated_live_cnt
        item['following_topic_cnt'] = following_topic_cnt
        item['following_column_cnt'] = following_column_cnt
        item['following_question_cnt'] = following_question_cnt
        item['following_question_cnt'] = following_question_cnt
        item['following_fav_list_cnt'] = following_fav_list_cnt

    def _parse_relationships(self, data, item):
        follower_cnt = data[self.follower_key]
        following_cnt = data[self.following_key]
        item['follower_cnt'] = follower_cnt
        item['following_cnt'] = following_cnt

    @staticmethod
    def _extract_entities(response):
        profile = response.xpath(
            '/html/body/div[@id="data"]/@data-state').extract_first()
        entities = json.loads(profile)['entities']['users']
        return entities

    def parse(self, response):
        if response.status == 400:
            return
        elif response.status != 200:
            return response.request.replace(dont_filter=True)
        if 'signin?next=' in response.url:
            return
        entities = self._extract_entities(response)
        data = list(entities.values())[0]
        _id = data.get('id', None)
        if not _id:
            return
        item = UserProfile({'_id': _id})

        self._parse_profile(data, item)
        self._parse_achievements(data, item)
        self._parse_activities(data, item)
        self._parse_relationships(data, item)
        item['status'] = 1

        yield item

        meta = {'src': _id}
        main_key = data[self.main_key]
        # Following
        url = self.followings_url.format(**{'user': main_key, 'offset': 0})
        yield Request(url, callback=self.parse_followings,
                      headers=self.headers, meta=meta)
        # Follower
        url = self.followers_url.format(**{'user': main_key, 'offset': 0})
        yield Request(url, callback=self.parse_followers,
                      headers=self.headers, meta=meta)

    def _parse_followers_and_followings(self, response, from_src):
        meta = response.meta
        src_id = meta['src']
        data = json.loads(response.text)
        for entity in data['data']:
            _id = entity['id']
            if _id == src_id:
                continue
            # Build relationship
            if from_src:
                src = src_id
                dst = _id
            else:
                src = _id
                dst = src_id
            yield FollowRelationShip({'user_id': src, 'following_id': dst})

            main_key = entity[self.main_key]
            url = self.people_url.format(**{'user' :main_key})
            yield Request(url, callback=self.parse, headers=self.headers,
                          priority=10)

        if not data['paging']['is_end']:
            url = data['paging']['next']
            if from_src:
                callback = self.parse_followings
            else:
                callback = self.parse_followers
            yield Request(url, callback=callback,
                          headers=self.headers, meta=meta)

    def parse_followings(self, response):
        yield from self._parse_followers_and_followings(response, True)

    def parse_followers(self, response):
        yield from self._parse_followers_and_followings(response, False)


class APIPeopleSpider(PeopleSpider):
    name = 'mpeople'
    allowed_domains = ['zhihu.com']
    people_url = 'https://api.zhihu.com/people/{user}'
    followings_url = ('https://api.zhihu.com/people/{user}/'
                      'followees?limit=20&offset={offset}')
    followers_url = ('https://api.zhihu.com/people/{user}/'
                     'followers?limit=20&offset={offset}')
    headers = {'authorization': ('Bearer 1.1hVNkAAAAAAALAAAAYAJVTVKuq1rcFz'
                                 'OMi21Ib991umxU7VFV5toN-A==')}

    # keys
    main_key = 'id'
    loc_key = 'location'
    emp_key = 'employment'
    edu_key = 'education'
    voteup_key = 'voteup_count'
    thanked_key = 'thanked_count'
    favorited_key = 'favorited_count'
    answer_key = 'answer_count'
    question_key = 'question_count'
    articles_key = 'articles_count'
    columns_key = 'columns_count'
    pins_key = 'pins_count'
    favorite_key = 'favorite_count'
    hosted_live_key = 'hosted_live_count'
    participated_live_key = 'participated_live_count'
    following_topic_key = 'following_topic_count'
    following_columns_key = 'following_columns_count'
    following_question_key = 'following_question_count'
    following_fav_list_key = 'following_favlists_count'
    follower_key = 'follower_count'
    following_key = 'following_count'

    def start_requests(self):
        fmt_dict = {'user': '0970f947b898ecc0ec035f9126dd4e08'}
        req = Request(self.people_url.format(**fmt_dict), headers=self.headers,
                      callback=self.parse)
        return [req]

    def parse(self, response):
        if response.status == 400:
            return
        elif response.status != 200:
            return response.request.replace(dont_filter=True)
        data = json.loads(response.text)
        _id = data['id']
        item = UserProfile({'_id': _id})

        self._parse_profile(data, item)
        self._parse_achievements(data, item)
        self._parse_activities(data, item)
        self._parse_relationships(data, item)
        item['status'] = 1

        yield item
        meta = {'src': _id}
        url = self.followings_url.format(**{'user': _id, 'offset': 0})
        yield Request(url, callback=self.parse_followings,
                      headers=self.headers, meta=meta)
        # Follower
        url = self.followers_url.format(**{'user': _id, 'offset': 0})
        yield Request(url, callback=self.parse_followers,
                      headers=self.headers, meta=meta)

    def _parse_profile(self, data, item):
        name = data['name']
        headline = replace_html_tag(data['headline'])
        gender = data['gender']
        locations = []
        if self.loc_key in data:
            locations = [x['name'] for x in data[self.loc_key]]
        business = data['business']['name'] if 'business' in data else ''
        employments = []
        if self.emp_key in data:
            for employment in data[self.emp_key]:
                company = employment[0]['name']
                job = ''
                if len(employment) > 1 and employment[1]:
                    job = employment[1]['name']
                employments.append('{}-{}'.format(company, job))
        educations = []
        if self.edu_key in data:
            for edu in data[self.edu_key]:
                educations.append(edu['name'])
        description = replace_html_tag(data['description'])

        item['name'] = name
        item['headline'] = headline
        item['gender'] = gender
        item['locations'] = locations
        item['business'] = business
        item['employments'] = employments
        item['educations'] = educations
        item['description'] = description
