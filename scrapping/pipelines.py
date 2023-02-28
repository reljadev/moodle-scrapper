# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import hashlib
import mimetypes
import os
import logging

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

from scrapy.http import Request
from scrapy.pipelines.files import FilesPipeline
from scrapy.settings import Settings
from scrapy.utils.python import to_bytes
from scrapy.exceptions import DropItem

class ScrappingPipeline(FilesPipeline):

	def process_item(self, item, spider):
		url = item['file_urls'][0]
		ext = url.split('.')[-1]
		#TODO: doesn't always work
		if ext == 'pdf':
			return super().process_item(item, spider)
		else:
			raise DropItem(f'Extension is {ext}')
	
	def get_media_requests(self, item, info):
		urls = ItemAdapter(item).get(self.files_urls_field, [])
		return [Request(u, meta={'course_title': item['course_title'], 'week_title': item['week_title'], 'file_name': item['file_name']}) for u in urls]

	def file_path(self, request, response=None, info=None, *, item=None):
		course_title = request.meta['course_title']
		week_title = request.meta['week_title']
		file_name = request.meta['file_name']
		media_ext = os.path.splitext(request.url)[1]
		# Handles empty and wild extensions by trying to guess the
		# mime type then extension or default to empty string otherwise
		if media_ext not in mimetypes.types_map:
			media_ext = ''
			media_type = mimetypes.guess_type(request.url)[0]
			if media_type:
				media_ext = mimetypes.guess_extension(media_type)
				
		return f'{course_title}/{week_title}/{file_name}{media_ext}'
