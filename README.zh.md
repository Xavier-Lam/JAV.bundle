# JAV.bundle
[![Donate with Bitcoin](https://en.cryptobadges.io/badge/micro/1BdJG31zinrMFWxRt2utGBU2jdpv8xSgju)](https://en.cryptobadges.io/donate/1BdJG31zinrMFWxRt2utGBU2jdpv8xSgju)


**JAV.bundle**是一个收集日本AV信息的[plex](https://plex.tv)代理。它从[JavLibrary](https://javlibrary.com/)、[AVEntertainments](https://www.aventertainments.com/)和一些工作室的官方网站收集数据。

这个代理目前只支持抓取日语内容，你可以创建一个pull请求来帮助我们支持其他语言。



## 安装
从[Github仓库](https://github.com/Xavier-Lam/JAV.bundle)下载最新的源码压缩包，然后解压到[Plex插件文件夹]((https://support.plex.tv/hc/en-us/articles/201106098-How-do-I-find-the-Plug-Ins-folder-))中。你可以按照[这篇介绍]((https://support.plex.tv/articles/201187656-how-do-i-manually-install-a-plugin/))来安装JAV.bundle。


### 使用
插件安装完毕后，你可以在Library的编辑页面选择`JAV`作为Library的代理，并使用`Plex Movie Scanner`作为Library的Scanner。

对于居住在中国大陆的用户，请确保你有能力访问代理抓取数据的网站。


### 配置
JAV.bundle代理有两个配置。是否使用cloudscraper库来抓取数据，以及发送请求时使用的用户代理字符串。

我不知道为什么有时cloudscraper会碰到一个意外的保护页面，当cloudscraper不能正常工作时，这些设置可能会起作用。



## 指引
### 文件命名和文件夹结构
对于有码AV，视频的名称或其父文件夹的名称必须包含视频的番号，使用空格或方括号将番号与标题的其他部分分开

* JBD-226
* [JBD-226]No Torture Remaining 4 Shinoda Yu
* JBD-226 No Torture Remaining 4 Shinoda Yu

对于从官方网站抓取的无码AV（包括[caribbeancom](https://caribbeancom.com), [1pondo](https://1pondo.tv), [heyzo](https://heyzo.com)和[tokyo-hot](https://tokyo-hot.com)），我建议用工作室的名字和视频的id来命名你的视频或文件夹

* 1Pondo 052611_102 Nozomi Hazuki
* Caribbean 111914-739 Facial For Mature 8 Part 1 Ryu Enami
* Heyzo 0796 Hamar's World 20 -Secrets about Miyuki- - Miyuki Ojima

对于其他无码AV，数据将从[AVEntertainments](https://aventertainments.com)爬取，你应该这样命名你的视频。

* [RED-052] Red Hot Fetish Collection Vol. 37 : Kiriya Anno
* [SKY-101] Sky Angel Vol.63 Sayaka Fukuhara


### 手动识别你的视频
有时你可能无法得到正确的视频匹配结果，特别是对于那些通过使用AVEntertainments代理收集的视频，它的匹配策略不是很好。你可以尝试在搜索标题栏中输入番号，以纠正匹配结果。



## 答谢
* 本项目受到[JAVLibrary.bundle](https://github.com/w-k-io/JAVLibrary.bundle)的影响，感谢[
w-k.io](https://github.com/w-k-io)。
* 女优的头像是由[gfriends](https://github.com/xinxin8816/gfriends)项目提供的。



## 捐助
* 我需要一个[oppaitime](https://oppaiti.me)和一个[馒头](https://kp.m-team.cc)的邀请，如果有人给我一个邀请，我将非常感激。