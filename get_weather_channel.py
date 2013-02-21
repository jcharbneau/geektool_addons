#!/usr/bin/env python
import sys,feedparser, re, htmlentitydefs, urllib2, string

from optparse import OptionParser

########################################################################################################
# the following function was found at: http://effbot.org/zone/re-sub.htm#unescape-html
########################################################################################################
def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)
########################################################################################################

########################################################################################################
# get_zip - get our zip, using the api key received from ipinfodb.com 
########################################################################################################
def get_zip(key):
     data = {}
     url = "api.ipinfodb.com"
     uri = "v3/ip-city/?key=%s" % key

     complete_url = "http://%s/%s" % (url,uri)
     response = urllib2.urlopen(complete_url)

     if response.code == 200:
	ip_content = response.read()

     else:
   	print 'Error connecting to the server!! Check your internet connection'
   	exit(1)

     data['zip'] = ip_content.split(';')[7]
     data['location'] = "%s, %s" % (ip_content.split(';')[6],ip_content.split(';')[5])

     return data
		

########################################################################################################
# my own hacked up code...
########################################################################################################
def get_weather(rss_feed_zip='45066'):
   # build our url with the zip being passed in
   rss_feed_url = 'feed://rss.weather.com/weather/rss/local/%s?cm_ven=LWO&cm_cat=rss&par=LWO_rss' % rss_feed_zip

   # retrieve our feed and parse it
   d = feedparser.parse(rss_feed_url)
 
   # compile a regex - this is a hack, just using it to search and replace all 
   #  occurances so that we don't show them (they're ugly and useless)
   p = re.compile("for more details\?", re.IGNORECASE)

   x = re.compile("your weekend forecast for ", re.IGNORECASE)

   # create a empty dict
   rarr = {}

   # loop through our entries in our returned rss data
   for detail in d['entries']:
   	# print detail

        # pull out a record from each, note this is embedded heirarchially, so we are digging
	#  down into the records value to parse what we need
	rec = detail['summary_detail']['value'].lower()
	location = x.sub("",unescape(detail['title'].lower()))

	# print "r:%s" % rec
	# replace all occurances of "for more details" with a single space " "
	rec = p.sub(" ",unescape(rec))
	

	# are we at the current weather piece
	if '<img alt=' in rec:
		# ok, we are, split out the image from the text - image is not used - yet
		for piece in rec.split('/>'):
			if '<img' in piece:
				rarr['current_img'] = "%s/>" % piece
			else:
				# Current weather
				rarr['current'] = "%s" % piece
					
		# break

	# if we are to the text & beyond, then that is the end of the data we are
	# interested in
	elif 'beyond' in rec:
		# create an empty list
		rforecast = []

		# split out our forecasts'
		for col in rec.split("----"):
			# if we're at the beyond column, then we don't need that data
			if "beyond" in col:
				continue
			# otherwise - we do, note the call to unescape and strip
			else:
				rforecast.append("%s" % unescape(col.strip()))

		# assign the forecast list to our dict
		rarr['forecast'] = rforecast
		break

	rarr['location'] = location

   # return the dict back to the caller
   return rarr


########################################################################################################
# implicit main
########################################################################################################
if __name__ == "__main__":

        # usage statement
        usage = "usage: %prog --key [infodb.com api key] --zip [force zip code] \n Specify either key or zip, if both are specified, then error will occur"

        #assign usage display to option parser
        parser = OptionParser(usage=usage) 

        # add key option
        parser.add_option("-k","--key", dest="key", help="InfoDB API Key - Register @ http://ipinfodb.com/\n") 

        # add zip over-ride option
        parser.add_option("-z","--zipcode", dest="zipcode", help="Specify the zip code\n")

        # check the length of our args and 
        # start the ball rolling....
        if(len(sys.argv) > 1):
		location = ""

	        # parse the options/args out
        	(options, args) = parser.parse_args() #load options into a dictionary and arguments into a list

		if options.zipcode and not options.key:
                	ret_array = get_weather(options.zipcode)
			location = "Location (by zip): %s" % options.zipcode

		elif options.key and not options.zipcode:
			# get the external ip closest to us (whatever the machine ends up with as its first hop 
			# onto the internet at large)
			data = get_zip(options.key)

			# now call our get_weather routine
			ret_array = get_weather(data['zip'])

		else:
			print "Error, you specified both options; choose either dynamic lookup (specifying a key), or static lookup, passing in your zipcode"
			exit(1)

		print "Location: %s\n" % ret_array['location'].title()
		print "Current weather:\n\t%s\n" % ret_array['current'].encode('utf-8').strip()
		print "Forecast:"
		for i in ret_array['forecast']:
	   		print "\t%s\n" %  i.encode('utf-8').strip()

        else:
        	parser.print_help()             
               	sys.exit(1)



