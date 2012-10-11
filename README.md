#Helper utilites for PGMC

At this point, it's an attendance helper for section reps.

To make it work, copy defaults.ini to whatever you want, and specify that filename at the command line like so:

python main.py yourconfig.ini

You'll need some python libraries and things, but you can figure that out.  
Once you've got that set, it will start up serving on the server you specified.

##This history is fake
Up until October 25 after about 1:00pm, this history is reconstructed from Vim swapfiles.
The config file parts are backported from now (the future!), because I didn't want to upload any
potentially sensitive stuff to Github.

I did, however, want to retain the history of how this thing came to be, because I'm weird like that,
and also because in the event that my Github serves as some kind of portfolio in the future, it provides
an additional insight into how my code evolves.

##On that note
This is the first time I've actually successfully used Python for a web app.  I think that in
the future [webapp2][wa2] won't be my framework of choice (outside of [GAE][gae], anyway), because while it's nominally
usable outside of GAE, there are several areas I'm discovering where GAE is an assumption, and things are harder
than they should be outside of GAE.  For instance, ([spoilers!][rs]) the StaticFileHandler having to be implemented
for something that's done in the app.yaml file in GAE.  I was determined to make it work anyway though, and it's
been a good learning experience if nothing else.  And it does seem like a decent little framework.  And for my needs -- 
a very lightweight, basic framework just to get a couple dynamic pages up and running that let me run Python in them --
it has served its purpose very well.

[gae]: https://developers.google.com/appengine/ "Google App Engine"
[wa2]: http://webapp-improved.appspot.com/ 
[rs]: http://tardis.wikia.com/wiki/River_Song "River Song - TARDIS Index File"
