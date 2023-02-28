import scrapy
import logging
from scrapy.utils.log import configure_logging
from ..items import ScrappingItem
#from .. import items

import json

import os

# params
URL = 'https://moodle.epfl.ch/login/index.php'
#URL = 'https://moodlearchive.epfl.ch/2020-2021/auth/tequila/index.php'
USERNAME = 'reljin'
PASSWORD = 'UdWqDl^371$M'
HEADERS = {'Origin': 'https://tequila.epfl.ch', 'Referer': 'https://tequila.epfl.ch/cgi-bin/tequila/requestauth', 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36'}

class MoodleSpider(scrapy.Spider):
	# name of the spider
	name = "moodle"
	
	# configure logging
	configure_logging(install_root_handler=False)
	logging.basicConfig(
		filename='log.txt',
		format='%(levelname)s: %(message)s',
		level=logging.INFO
		)
		
	dont_filter = True
	
	def start_requests(self):
		logging.info("STARTING REQUEST")
		yield scrapy.Request(url=URL, callback=self.login_request, method='GET', meta={'dont_redirect': True, 													  'dont_filter': True,
												  'handle_httpstatus_list': [302]})
		
	def login_request(self, response):
		logging.info("STARTING LOGIN")
		key = response.headers.getlist('Set-Cookie')[1].decode().split(";")[0].split("=")[1]
		login_payload = {
			'requestkey': key,
			'username': USERNAME,
			'password': PASSWORD
			}
		yield scrapy.FormRequest(HEADERS['Referer'], callback=self.after_login, method='POST',
					meta={'dont_redirect': False, 'dont_filter': True}, formdata=login_payload, headers=HEADERS)
		
	def after_login(self, response):
		logging.info("LOGGED IN")
		
		for course in response.xpath("//div[@class='row coc-course']//h3/a"):
			course_title = course.xpath("./@title").extract()[0]
			course_link = course.xpath("./@href").extract()[0]
			
			yield scrapy.Request(course_link, callback=self.download_course, meta={'title': course_title})
			
	def download_course(self, response):
		course_title = response.meta['title']
		logging.info(course_title)
		
		# download public forum
		for forum in response.xpath("//li[@id='section-0']//li[@class='activity forum modtype_forum ']"):
			forum_link = forum.xpath(".//a/@href").extract()[0]
			forum_title = forum.xpath(".//span[@class='instancename']/text()").extract()[0]
			
			yield scrapy.Request(url=forum_link, callback=self.download_forum, meta={'course_title': course_title,
												    'forum_title': forum_title})
		
		# download resources for each week
		for week in response.xpath("//li[boolean(number(substring-after(@id, 'section-')))]"):
			week_title = week.xpath(".//h3//a/text()").extract()[0]
			logging.info(week_title)
			for resource in week.xpath(".//li[starts-with(@class, 'activity ')]"):
				resource_name = resource.xpath(".//span[@class='instancename']/text()").extract()[0]
				#TODO: catch index out of range
				try:
					resource_link = resource.xpath(".//a/@href").extract()[0]
				except IndexError:
					pass
				yield scrapy.Request(url=resource_link+'&redirect=1', callback=self.download_resource,
							meta={'course_title': course_title, 'week_title': week_title,
								'resource_name': resource_name})
		
	def download_forum(self, response):
		# download page source
		path = '/media/relja/Data/FAKS/EPFL/STUDIJE/2020-21/'
		filename = os.path.join(path, response.meta['course_title'], response.meta['forum_title'], response.meta['forum_title']) + '.html'
		#logging.info("FILENAME " + filename)
		self.download_page(filename, response.body)
		
		for topic in response.xpath("//tr[@class='discussion subscribed']//div[@class='p-3 p-l-0']"):
			topic_title = topic.xpath(".//a/@title").extract()[0]
			topic_link = topic.xpath(".//a/@href").extract()[0]
			
			#TODO: name of the folder and course
			yield scrapy.Request(url=topic_link, callback=self.download_topic_2, meta={'topic_title': topic_title,
												      'course_title': response.meta['course_title'],
												      'forum_title': response.meta['forum_title']})
												    
	def download_topic_2(self, response):
		#download topic page
		path = '/media/relja/Data/FAKS/EPFL/STUDIJE/2020-21/'
		filename = os.path.join(path, response.meta['course_title'], response.meta['forum_title'], response.meta['topic_title']) + '.html'
		self.download_page(filename, response.body)
			
	def download_page(self, filename, content):
		#TODO: automatically escape special characters
		dirname = os.path.dirname(filename)
		if not os.path.exists(dirname):
			os.makedirs(dirname)
		with open(filename, 'wb') as f:
			f.write(content)
		
	# NOT USED	
	def download_topic(self, response):
		# save first post
		# TODO: first post can be in the download_post as well
		discussion_title = response.meta['topic_title']
		first_post = response.xpath("//div[@class='d-flex border p-2 mb-2 forumpost focus-target  firstpost starter']")
		discussion = {}
		discussion['author'] = first_post.xpath(".//div[@class='mb-3']//a/text()").extract()[0]
		discussion['time'] = first_post.xpath(".//div[@class='mb-3']//time/text()").extract()[0]
		try:
			#TODO: loop through all paragraphs and concate
			#TODO: download images
			#TODO: download latex formulas
			discussion['text'] = (first_post.xpath(".//div[@class='post-content-container']/p/text()").extract()[0])
			#logging.info(discussion['text'])
		except IndexError:
			logging.info("NO TEXT ERROR ! ! !")
			logging.info(response.meta['course_title'])
			logging.info(discussion_title)
			logging.info(discussion['author'])
			logging.info(discussion['time'])
		discussion['replies'] = []
				
		# save all replies recursively
		#for reply in response.xpath("//div[@data-content='forum-discussion']/article/div[@data-region='replies-container']/article"):
			#discussion['replies'].append(download_post(reply))
			
		# save json to a file
		
		#logging.info("SAVING DISCUSSION ! ! ! !")
		#with open(discussion_title + '.txt', 'w') as file:
		#	json.dump(discussion, file, ensure_ascii=False)
		
	# NOT USED	
	def download_post(self, post):
		discussion = {}
		discussion['author'] = post.xpath("./div[@class='d-flex border p-2 mb-2 forumpost focus-target  ']//div[@class='mb-3']/a/text()").extract()[0]
		discussion['time'] = post.xpath("./div[@class='d-flex border p-2 mb-2 forumpost focus-target  ']//div[@class='mb-3']/time/text()").extract()[0]
		discussion['text'] = post.xpath("./div[@class='d-flex border p-2 mb-2 forumpost focus-target  ']//p/text()").extract()[0]
		discussion['replies'] = []
		
		for reply in post.xpath("./div[@data-region='replies-container']/article"):
			discussion['replies'].append(download_post(reply))
			
		return discussion
				
	def download_resource(self, response):
		item = ScrappingItem()
		item['file_name'] = response.meta['resource_name']
		item['file_urls'] = [response.url]
		item['course_title'] = response.meta['course_title']
		item['week_title'] = response.meta['week_title']
		return item 
	    
    

