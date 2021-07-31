# JAV.bundle
[![Donate with Bitcoin](https://en.cryptobadges.io/badge/micro/1BdJG31zinrMFWxRt2utGBU2jdpv8xSgju)](https://en.cryptobadges.io/donate/1BdJG31zinrMFWxRt2utGBU2jdpv8xSgju)

[中文版Readme](README.zh.md)

**JAV.bundle** is a [plex](https://plex.tv) agent for Japanese porn videos. It collects data from [JavLibrary](https://javlibrary.com/), [AVEntertainments](https://www.aventertainments.com/) and some studio's official sites.


## Installation
Download the latest source zip from [repository](https://github.com/Xavier-Lam/JAV.bundle),then unzip the zip file to the [Plex plugin folder](https://support.plex.tv/hc/en-us/articles/201106098-How-do-I-find-the-Plug-Ins-folder-).

You can follow [this instruction](https://support.plex.tv/articles/201187656-how-do-i-manually-install-a-plugin/) to install JAV.bundle.

After installing this plugin, you can select `JAV` as your library's agent in your library's edit page, and you should use `Plex Movie Scanner` as the library's scanner.

For users in mainland of PR China, please make sure you have ability to access the sites which the agent crawls data from, these sites may be blocked by your government.


## Quickstart
### Naming and organizing your videos
For censored videos, the video's name or its parent folder's name must contains the video id, using space or square bracket to split from the other parts of title like these:

* JBD-226
* [JBD-226]No Torture Remaining 4 Shinoda Yu
* JBD-226 No Torture Remaining 4 Shinoda Yu

For uncensored videos, I recommend naming your video or parent folder by including both studio's name and the video's id:

* 1Pondo 052611_102 Nozomi Hazuki
* Caribbean 111914-739 Facial For Mature 8 Part 1 Ryu Enami
* Heyzo 0796 Hamar's World 20 -Secrets about Miyuki- - Miyuki Ojima

For those older uncensored video whose studio has closed down, I recommend naming your video like this:

* [RED-052] Red Hot Fetish Collection Vol. 37 : Kiriya Anno
* [SKY-101] Sky Angel Vol.63 Sayaka Fukuhara

### Manual identify your video
Sometimes you may not get the correct match of the video from JAV.bundle, especially for the AVEntertainments agent, its match strategy is not very good. You can try to type the id of your video in the title field to correct the match result.


## Contribute to this project
You can create an issue to report bugs. Please descript your problem, provide the movie id or search conditions that you meet the problem. And upload your log file which located in your *[Plex Media Server data directory](https://support.plex.tv/articles/202915258-where-is-the-plex-media-server-data-directory-located/)/Logs/PMS Plugin Logs/* folder and named with *com.plexapp.agents.jav.log*.

I am not going to develop new feature or add new data sources. You can create a pull request to contribute to this project if you wish. 

As the development document of plex plugin has been removed, you can check out [this archive](https://web.archive.org/web/20150107154037/http://dev.plexapp.com/docs/index.html) to learn how to develop a plex plugin.

### Credits
* This project is influenced by [JAVLibrary.bundle](https://github.com/w-k-io/JAVLibrary.bundle), thanks to [
w-k.io](https://github.com/w-k-io).
* The actresses' avatars provide by [gfriends](https://github.com/xinxin8816/gfriends) project.

### TODOS:
* JAVLibrary agent