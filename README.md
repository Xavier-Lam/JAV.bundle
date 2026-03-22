# JAV.bundle
[![test](https://github.com/Xavier-Lam/JAV.bundle/actions/workflows/test.yml/badge.svg)](https://github.com/Xavier-Lam/JAV.bundle/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/Xavier-Lam/JAV.bundle/branch/master/graph/badge.svg)](https://codecov.io/gh/Xavier-Lam/JAV.bundle)

**JAV.bundle** is a [plex](https://plex.tv) agent plugin gathering metadata for Japanese adult videos, the metadata includes but not limited to release date, studio, genres, actresses, posters and trailers. It crawls data from [JAVLibrary](https://javlibrary.com), [DMM](https://www.dmm.co.jp) and some studios' official sites.

I recently completely rewrote the plugin, it should be seamlessly migrated from the legacy version, please read [Migrate from legacy version](#migrate-from-legacy-version) for more information. The new version is more powerful and maintainable, I strongly recommend you to upgrade to the newest version.

## Installation
Download the latest plugin bundle zip from [Releases](https://github.com/Xavier-Lam/JAV.bundle/releases), then unzip the zip file to the [Plex plugin folder](https://support.plex.tv/hc/en-us/articles/201106098-How-do-I-find-the-Plug-Ins-folder-). You can follow [this guide](https://support.plex.tv/articles/201187656-how-do-i-manually-install-a-plugin/) to install the plugin.

> Note: Don't just overwrite the old plugin folder when you are updating the plugin, delete the old plugin folder first, then install the new version.

### Install from source code
You can also install the plugin from source code if you want experience the latest features. Clone or download this repository and copy the `JAV.bundle` folder to your Plex plugin folder.

## Usage
After the plugin has been installed, choose `JAV (V2)` as the agent in your library's edit page, and you should use `Plex Movie Scanner` as the library's scanner.

### Naming and organizing your videos
For censored videos, the video's filename or its parent folder's name must contain the video code, using space or square bracket to split the code from other parts of title like these:

* JBD-226
* [JBD-226] No Torture Remaining 4 Shinoda Yu
* JBD-226 No Torture Remaining 4 Shinoda Yu

For the uncensored videos, except for the video code, you have to include the studio name in its filename or its parent folder's name.

* 1Pondo 052611_102 Nozomi Hazuki
* Caribbean 111914-739 Facial For Mature 8 Part 1 Ryu Enami
* Heyzo 0796 Hamar's World 20 -Secrets about Miyuki - Miyuki Ojima

> Sometimes you may not get the correct match results for your video, you can try to fill the code of your video in the title field to correct the match results.

## Migrate from legacy version
The v2 version is backward compatible with the [legacy version](https://github.com/Xavier-Lam/JAV.bundle/tree/legacy), you can simply switch to the new version in your library's configuration. 

After switching to the new version, it is recommended to configure the new options in the plugin settings first. After configuring the options, you can run `Refresh All Metadata` to get the new metadata for all your videos.

If you care very much about the current metadata in your library, please [back up your database](https://support.plex.tv/articles/201539237-backing-up-plex-media-server-data/) before switching to the new version.

The new version is completely rewritten, and the codebase does not share any history with the legacy version.

### New features
The major new features of v2 version are:

* Add new sources include `DMM` and `MGStage`
* Scrape trailers from `DMM` and some studios' official sites
* Actresses name correction via `seesaawiki`
* Scrape series data from sources and optionally organize series into collections
* Improve similarity recommendation by telling keywords to plex media server (how plex media server handles these keywords is unknown, the experience may worse for some users)

There are also some minor improvements not mentioned here.

### Differences between legacy version and v2
* `FC2` and `AVE` agents are not available for now, I am actively working on it.
* `JAVDB` agent is dropped because it only provides English and Traditional Chinese metadata, which is not consistent with other agents that provide Japanese metadata. If the project further supports multiple languages, I may add it back.

## Agents
The plugin consists of multiple sub-agents:

| Agent | Enabled | Priority | Description |
| --- | --- | --- | --- |
| JAVLibrary | Yes | 900 | A portal site for censored Japanese adult videos, the primary contributor |
| DMM | Yes | 800 | A portal site for censored Japanese adult videos, contribute some additional metadata and trailers, if *JAVLibrary* is not available, it can work as a primary agent for censored videos |
| MGStage | Yes | 500 | Official site of *Prestige* studio, some videos from *Prestige* are not available in *JAVLibrary* and *DMM*, it can complement the above two agents |
| Caribbean, Caribpr, 1Pondo, Heyzo, Tokyo-Hot | Yes | 500 | Official sites of uncensored videos |
| Seesaawiki | Yes | -100 | A wiki site for Japanese adult video actresses, it can correct the actresses' names |
| Warashi | Yes | -200 | Provide actresses' avatars |
| GFriends | Yes | -300 | A fall back agent for actresses' avatars |

You are able to disable some of the agents in the plugin settings, `DMM` and `MGStage` agents are not available in some regions.

### JAVLibrary
To use [JAVLibrary](https://javlibrary.com) agent, you have to bypass the *cloudflare* challenge. There are two ways to bypass the challenge, one is using [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr), if you are able to set up a *FlareSolverr* instance, it would be much more convenient. The other is [manually filling](https://github.com/Xavier-Lam/JAV.bundle/blob/legacy/README.md#legacy) the `User-Agent` header and `cf_clearance` cookie value everytime in the agent's configuration.

#### FlareSolverr
If you've set up a [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) instance, you can fill its URL in the agent's configuration to make the agent bypass the *cloudflare* challenge via *FlareSolverr*. It is the most convenient way to bypass the challenge. If a *FlareSolverr* URL is not provided, the agent will try to access *JAVLibrary* using the legacy way.

It uses [FlareSolverrSession](https://github.com/Xavier-Lam/FlareSolverrSession) to manage the session with *FlareSolverr*.

## Design
There is only a main agent `JAVAgent` to dispatch the search and metadata updating to multiple sub-agents. The sub-agents are executed in a priority order, the higher prioritized agent will contribute metadata first. Generally, the lower prioritized agent won't override an attribute set by a higher prioritized agent, but if the agent has more confidence on that attribute, it may "opinionatedly" override it. For example, official sites of studios usually have more confidence on the release date and a higher quality of poster, it will override these attributes even if their priority is lower.

## Troubleshooting
* **Nothing works, the agent doesn't match any videos**

    Please make sure you can access those websites on your plex server, if not, consider setting up a proxy for the plugin in the plugin settings

* **The `JAV (V2)` agent doesn't show up in the agent list**

    Since *PMS* 1.43.0, legacy agents won't show up by default when creating a new library. Enable `Show Legacy Agent during library set up` under `Server Settings > Library` to show legacy agents. You can look up the [instructions](https://support.plex.tv/articles/200241558-agents/) for more details.

* **Trailers won't play in Plex**

    Some trailers are only available in some regions, the proxy setting in the plugin won't help in loading trailers because the request is made by Plex Media Server instead of the plugin. You can consider setting up a [sidecar proxy](https://github.com/Xavier-Lam/proxy-sidecar) if you are running your Plex Media Server in a docker container.

## Contribute to this project
Any contribution is welcome, if you have any issue with a specific video, you can create an issue to report the problem. When submitting an issue, please provide your log file which located in your *[Plex Media Server data directory](https://support.plex.tv/articles/202915258-where-is-the-plex-media-server-data-directory-located/)/Logs/PMS Plugin Logs/com.plexapp.agents.jav.log*. I won't spend much time on the project, don't expect all issues will be resolved.

As the development document of plex plugin has been removed, you can check out [the documentation](https://plex-plugin-docs.readthedocs.io/en/latest/) to learn how to develop a plex plugin. Please pass the unittests before submitting a PR, and write tests for your code.

## Credits
* This project is influenced by [JAVLibrary.bundle](https://github.com/w-k-io/JAVLibrary.bundle), thanks to [w-k.io](https://github.com/w-k-io).
* The actresses' avatars are provided by [gfriends](https://github.com/xinxin8816/gfriends) project.

## Donate
* I am looking for a [m-team](https://kp.m-team.cc) invitation, I'll be very appreciated if someone gives me one.
