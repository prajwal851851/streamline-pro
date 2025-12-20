# scraper/scraper/pipelines.py
from itemadapter import ItemAdapter
from streaming.models import Movie, StreamingLink
from twisted.internet import threads

class DjangoItemPipeline:
    def process_item(self, item, spider):
        # Use Twisted's deferToThread to run Django ORM in a separate thread
        return threads.deferToThread(self._process_item_sync, item, spider)
    
    def _process_item_sync(self, item, spider):
        """Synchronous processing of item in a separate thread"""
        adapter = ItemAdapter(item)

        # Determine if this is old MovieItem or new StreamingItem format
        if 'stream_url' in adapter.keys():
            # OLD FORMAT from goojara spider (MovieItem)
            return self._process_old_format(adapter, spider)
        elif 'links' in adapter.keys():
            # NEW FORMAT from oneflix/fawesome spiders (StreamingItem)
            return self._process_new_format(adapter, spider)
        else:
            spider.logger.warning(f"Unknown item format: {adapter.keys()}")
            return item

    def _process_old_format(self, adapter, spider):
        """Process old MovieItem format (goojara spider)"""
        # Create or update the Movie
        movie_defaults = {
            'title': adapter.get('title'),
            'year': adapter.get('year'),
            'synopsis': adapter.get('synopsis'),
            'poster_url': adapter.get('poster_url'),
            'type': 'movie',  # goojara only does movies
            'original_detail_url': adapter.get('source_url'),  # Map source_url to original_detail_url
        }
        
        movie, created = Movie.objects.update_or_create(
            imdb_id=adapter.get('imdb_id'),
            defaults=movie_defaults
        )

        # Create or update the StreamingLink
        if adapter.get('stream_url'):
            link_defaults = {
                'quality': adapter.get('quality', 'HD'),
                'language': adapter.get('language', 'EN'),
                'is_active': True,
            }
            
            link, link_created = StreamingLink.objects.update_or_create(
                movie=movie,
                source_url=adapter.get('stream_url'),
                defaults=link_defaults
            )
            
            if link_created:
                spider.logger.info(f'Created new link for {movie.title}')
            else:
                spider.logger.info(f'Updated link for {movie.title}')
        
        return adapter.asdict()

    def _process_new_format(self, adapter, spider):
        """Process new StreamingItem format (oneflix/fawesome spiders)"""
        # Create or update the Movie
        movie_defaults = {
            'title': adapter.get('title'),
            'year': adapter.get('year'),
            'type': adapter.get('type', 'movie'),
            'synopsis': adapter.get('synopsis'),
            'poster_url': adapter.get('poster_url'),
            'original_detail_url': adapter.get('original_detail_url'),
        }
        
        movie, created = Movie.objects.update_or_create(
            imdb_id=adapter.get('imdb_id'),
            defaults=movie_defaults
        )

        # Process streaming links
        links = adapter.get('links', [])
        if links:
            for link_data in links:
                link_defaults = {
                    'quality': link_data.get('quality', 'HD'),
                    'language': link_data.get('language', 'EN'),
                    'is_active': link_data.get('is_active', True),
                }
                
                link, link_created = StreamingLink.objects.update_or_create(
                    movie=movie,
                    source_url=link_data.get('source_url'),
                    defaults=link_defaults
                )
                
                if link_created:
                    spider.logger.info(f'Created new link for {movie.title}')
        else:
            spider.logger.warning(f'No streaming links for {movie.title}')
        
        return adapter.asdict()