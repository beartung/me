DROP TABLE IF EXISTS `me_user`;
CREATE TABLE `me_user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `email` varchar(64) NOT NULL DEFAULT '',
  `password` varchar(15) NOT NULL DEFAULT '',
  `time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `me_card`;
CREATE TABLE `me_card` (
  `user_id` int(11) NOT NULL DEFAULT '0',
  `uid` varchar(15) NOT NULL DEFAULT '0',
  `email` varchar(64) NOT NULL DEFAULT '',
  `skype` varchar(64) NOT NULL DEFAULT '',
  `name` varchar(64) NOT NULL DEFAULT '',
  `alias` varchar(64) NOT NULL DEFAULT '',
  `phone` varchar(64) NOT NULL DEFAULT '',
  `photo` int(11) NOT NULL DEFAULT '0',
  `score` int(11) NOT NULL DEFAULT '0',
  `activities` int(11) NOT NULL DEFAULT '0',
  `flag` char(1) NOT NULL DEFAULT 'N',
  `join_time` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `rtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `ctime` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  PRIMARY KEY (`user_id`),
  KEY `idx_uid` (`uid`,`user_id`),
  KEY `idx_email` (`email`,`user_id`),
  KEY `idx_skype` (`skype`,`user_id`),
  KEY `idx_alias` (`alias`,`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `me_profile`;
CREATE TABLE `me_profile` (
  `user_id` int(11) NOT NULL DEFAULT '0',
  `sex` char(1) NOT NULL DEFAULT '0',
  `love` char(2) NOT NULL DEFAULT '0',
  `zodiac` char(2) NOT NULL DEFAULT '0',
  `astro` char(2) NOT NULL DEFAULT '0',
  `birthday` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `marriage` char(2) NOT NULL DEFAULT '0',
  `province` varchar(64) NOT NULL DEFAULT '',
  `hometown` varchar(64) NOT NULL DEFAULT '',
  `weibo` varchar(64) NOT NULL DEFAULT '',
  `instagram` varchar(64) NOT NULL DEFAULT '',
  `blog` varchar(128) NOT NULL DEFAULT '',
  `code` varchar(64) NOT NULL DEFAULT '',
  `github` varchar(64) NOT NULL DEFAULT '',
  `resume` varchar(128) NOT NULL DEFAULT '',
  `intro` varchar(512) NOT NULL DEFAULT '',
  `rtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`),
  KEY `idx_sex` (`sex`,`user_id`),
  KEY `idx_astro` (`astro`,`user_id`),
  KEY `idx_zodiac` (`zodiac`,`user_id`),
  KEY `idx_birth` (`birthday`,`user_id`),
  KEY `idx_province` (`province`,`user_id`),
  KEY `idx_hometown` (`hometown`,`user_id`),
  KEY `idx_code` (`code`,`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `me_like`;
CREATE TABLE `me_like` (
  `user_id` int(11) NOT NULL DEFAULT '0',
  `liker_id` int(11) NOT NULL DEFAULT '0',
  `rtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`, `liker_id`),
  KEY (`liker_id`, `user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `me_tag`;
CREATE TABLE `me_tag` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(128) NOT NULL DEFAULT '',
  `rtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `me_stats`;
CREATE TABLE `me_stats` (
    `user_id` int(11) NOT NULL DEFAULT '0',
    `n_like` smallint(6)  NOT NULL DEFAULT '0',
    `n_comment` smallint(6)  NOT NULL DEFAULT '0',
    `n_tag` smallint(6)  NOT NULL DEFAULT '0',
    `n_nofity` smallint(6)  NOT NULL DEFAULT '0',
    `n_blog` smallint(6)  NOT NULL DEFAULT '0',
    PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `me_user_tag`;
CREATE TABLE `me_user_tag` (
      `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
      `user_id` int(11) NOT NULL DEFAULT '0',
      `tagger_id` int(11) NOT NULL DEFAULT '0',
      `tag_id` int(11) NOT NULL DEFAULT '0',
      `rtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (`id`),
      UNIQUE KEY `uk_user_tagger_tag` (`user_id`,`tagger_id`,`tag_id`),
      KEY `k_tag` (`tag_id`, `user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `me_comment`;
CREATE TABLE `me_comment` (
      `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
      `user_id` int(11) NOT NULL DEFAULT '0',
      `author_id` int(11) NOT NULL DEFAULT '0',
      `content` varchar(512) NOT NULL DEFAULT '',
      `rtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (`id`),
      KEY `k_card` (`user_id`, `id`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `me_notify`;
CREATE TABLE `me_notify` (
      `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
      `user_id` int(11) NOT NULL DEFAULT '0',
      `author_id` int(11) NOT NULL DEFAULT '0',
      `flag` char(1) NOT NULL DEFAULT 'N',
      `ntype` char(2) NOT NULL DEFAULT 'L',
      `extra` varchar(512) NOT NULL DEFAULT '',
      `rtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (`id`),
      KEY `k_card` (`user_id`, `flag`, `id`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `me_badage`;
CREATE TABLE `me_badage` (
      `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
      `name` varchar(64) NOT NULL DEFAULT '',
      `icon` varchar(64) NOT NULL DEFAULT '',
      `extra` varchar(512) NOT NULL DEFAULT '',
      `intro` varchar(64) NOT NULL DEFAULT '',
      `rtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (`id`),
      UNIQUE KEY `k_name` (`name`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `me_user_badage`;
CREATE TABLE `me_user_badage` (
      `user_id` int(11) NOT NULL DEFAULT '0',
      `badage_id` int(11) NOT NULL DEFAULT '0',
      `rtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (`user_id`, `badage_id`),
      KEY `k_badage` (`badage_id`, `user_id`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `me_event`;
CREATE TABLE `me_event` (
      `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
      `author_id` int(11) NOT NULL DEFAULT '0',
      `name` varchar(64) NOT NULL DEFAULT '',
      `content` varchar(512) NOT NULL DEFAULT '',
      `photo` int(11) NOT NULL DEFAULT '0',
      `online_date` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
      `user_ids` varchar(512) NOT NULL DEFAULT '',
      `extra` varchar(512) NOT NULL DEFAULT '',
      `rtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (`id`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `me_event_photo`;
CREATE TABLE `me_event_photo` (
      `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
      `event_id` int(11) NOT NULL DEFAULT '0',
      `author_id` int(11) NOT NULL DEFAULT '0',
      `rtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (`id`),
      KEY `idx_uid` (`author_id`,`id`),
      KEY `idx_evt` (`event_id`,`id`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `me_photo_comment`;
CREATE TABLE `me_photo_comment` (
      `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
      `photo_id` int(11) NOT NULL DEFAULT '0',
      `author_id` int(11) NOT NULL DEFAULT '0',
      `content` varchar(512) NOT NULL DEFAULT '',
      `rtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (`id`),
      KEY `idx_photo` (`photo_id`, `id`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `me_photo_like`;
CREATE TABLE `me_photo_like` (
  `photo_id` int(11) NOT NULL DEFAULT '0',
  `liker_id` int(11) NOT NULL DEFAULT '0',
  `rtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`photo_id`, `liker_id`),
  KEY (`liker_id`, `photo_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `me_blog`;
CREATE TABLE `me_blog` (
      `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
      `user_id` int(11) NOT NULL DEFAULT '0',
      `flag` char(1) NOT NULL DEFAULT 'N',
      `btype` char(2) NOT NULL DEFAULT 'B',
      `action` char(2) NOT NULL DEFAULT 'N',
      `content` mediumtext NOT NULL DEFAULT '',
      `extra` varchar(512) NOT NULL DEFAULT '',
      `photo_id` int(11) NOT NULL DEFAULT '0',
      `audio_id` int(11) NOT NULL DEFAULT '0',
      `n_like` smallint(6)  NOT NULL DEFAULT '0',
      `n_unlike` smallint(6)  NOT NULL DEFAULT '0',
      `n_comment` smallint(6)  NOT NULL DEFAULT '0',
      `ctime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (`id`),
      KEY `k_flag` (`flag`, `id`),
      KEY `k_card` (`user_id`, `id`),
      KEY `k_photo` (`user_id`, `photo_id`),
      KEY `k_audio` (`user_id`, `audio_id`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `me_blog_comment`;
CREATE TABLE `me_blog_comment` (
      `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
      `blog_id` int(11) NOT NULL DEFAULT '0',
      `author_id` int(11) NOT NULL DEFAULT '0',
      `photo_id` int(11) NOT NULL DEFAULT '0',
      `content` varchar(512) NOT NULL DEFAULT '',
      `rtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (`id`),
      KEY `k_blog` (`blog_id`, `id`),
      KEY `k_author` (`author_id`, `id`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `me_blog_like`;
CREATE TABLE `me_blog_like` (
  `blog_id` int(11) NOT NULL DEFAULT '0',
  `liker_id` int(11) NOT NULL DEFAULT '0',
  `rtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`blog_id`, `liker_id`),
  KEY (`liker_id`, `blog_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `me_blog_unlike`;
CREATE TABLE `me_blog_unlike` (
  `blog_id` int(11) NOT NULL DEFAULT '0',
  `unliker_id` int(11) NOT NULL DEFAULT '0',
  `rtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`blog_id`, `unliker_id`),
  KEY (`unliker_id`, `blog_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `me_blog_photo`;
CREATE TABLE `me_blog_photo` (
      `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
      `blog_id` int(11) NOT NULL DEFAULT '0',
      `author_id` int(11) NOT NULL DEFAULT '0',
      `ftype` char(4) NOT NULL DEFAULT 'jpg',
      `rtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (`id`),
      KEY `idx_uid` (`author_id`,`id`),
      KEY `idx_blog` (`blog_id`,`id`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `me_topic`;
CREATE TABLE `me_topic` (
      `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
      `name` varchar(128) NOT NULL DEFAULT '',
      `rtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (`id`),
      UNIQUE KEY `idx_name` (`name`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `me_topic_blog`;
CREATE TABLE `me_topic_blog` (
      `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
      `user_id` int(10) NOT NULL DEFAULT '0',
      `topic_id` int(11) unsigned NOT NULL,
      `blog_id` int(11) unsigned NOT NULL,
      `rtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (`id`),
      UNIQUE KEY `uk_topic_blog` (`topic_id`,`blog_id`),
      KEY `blog_topic` (`blog_id`, `topic_id`),
      KEY `user_topic` (`user_id`, `topic_id`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `me_blog_audio`;
CREATE TABLE `me_blog_audio` (
      `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
      `blog_id` int(11) NOT NULL DEFAULT '0',
      `author_id` int(11) NOT NULL DEFAULT '0',
      `ftype` char(4) NOT NULL DEFAULT 'mp3',
      `rtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (`id`),
      KEY `idx_uid` (`author_id`,`id`),
      KEY `idx_blog` (`blog_id`,`id`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `me_question`;
CREATE TABLE `me_question` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL DEFAULT '0',
  `author_id` int(11) NOT NULL DEFAULT '0',
  `content` varchar(512) NOT NULL DEFAULT '',
  `flag` char(1) NOT NULL DEFAULT 'N',
  `rtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user` (`user_id`, `id`),
  KEY `idx_author` (`author_id`, `id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `me_answer`;
CREATE TABLE `me_answer` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `question_id` int(11) NOT NULL DEFAULT '0',
  `author_id` int(11) NOT NULL DEFAULT '0',
  `blog_id` int(11) NOT NULL DEFAULT '0',
  `rtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_q` (`question_id`, `id`),
  KEY `idx_author` (`author_id`, `id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `me_photo_tag`;
CREATE TABLE `me_photo_tag` (
    `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
    `photo_id` int(11) NOT NULL DEFAULT '0',
    `user_id` int(11) NOT NULL DEFAULT '0',
    `author_id` int(11) NOT NULL DEFAULT '0',
    `left` int(11) NOT NULL DEFAULT '0',
    `top` int(11) NOT NULL DEFAULT '0',
    `width` int(11) NOT NULL DEFAULT '0',
    `height` int(11) NOT NULL DEFAULT '0',
    `rtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_photo` (`photo_id`, `id`),
    KEY `idx_author` (`author_id`, `id`),
    KEY `idx_user` (`user_id`, `id`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `me_group`;
CREATE TABLE `me_group` (
    `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
    `uid` varchar(64) NOT NULL DEFAULT '',
    `name` varchar(256) NOT NULL DEFAULT '',
    `m_name` varchar(128) NOT NULL DEFAULT '',
    `intro` varchar(512) NOT NULL DEFAULT '',
    `photo` int(11) NOT NULL DEFAULT '0',
    `user_id` int(11) NOT NULL DEFAULT '0',
    `flag` char(1) NOT NULL DEFAULT 'N',
    `n_tag` smallint(6)  NOT NULL DEFAULT '0',
    `n_member` smallint(6)  NOT NULL DEFAULT '0',
    `n_thread` smallint(6)  NOT NULL DEFAULT '0',
    `ctime` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
    `rtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `idx_uid` (`uid`),
    KEY `idx_user` (`user_id`, `id`),
    KEY `idx_flag` (`flag`, `id`),
    KEY `idx_name` (`name`, `id`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `me_group_tag`;
CREATE TABLE `me_group_tag` (
      `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
      `group_id` int(11) NOT NULL DEFAULT '0',
      `tagger_id` int(11) NOT NULL DEFAULT '0',
      `tag_id` int(11) NOT NULL DEFAULT '0',
      `rtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (`id`),
      UNIQUE KEY (`group_id`,`tagger_id`,`tag_id`),
      KEY `k_tag` (`tag_id`, `group_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `me_group_member`;
CREATE TABLE `me_group_member` (
    `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
    `group_id` int(11) unsigned NOT NULL,
    `user_id` int(11) unsigned NOT NULL,
    `rtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY (`group_id`, `user_id`),
    KEY (`user_id`, `group_id`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `me_thread`;
CREATE TABLE `me_thread` (
    `id` int(11) unsigned NOT NULL, 
    `title` varchar(256) NOT NULL DEFAULT '',
    `group_id` int(11) unsigned NOT NULL,
    `author_id` int(11) unsigned NOT NULL,
    `n_comment` smallint(6)  NOT NULL DEFAULT '0',
    `flag` char(1) NOT NULL DEFAULT 'N',
    `rtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY (`group_id`, `flag`, `id`),
    KEY (`author_id`, `id`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `me_thread_comment`;
CREATE TABLE `me_thread_comment` (
    `id` int(11) unsigned NOT NULL,
    `group_id` int(11) unsigned NOT NULL,
    `thread_id` int(11) unsigned NOT NULL,
    `author_id` int(11) unsigned NOT NULL,
    `rtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`thread_id`, `id`),
    KEY (`author_id`, `id`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;
