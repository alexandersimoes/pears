CREATE TABLE "user" (email text, password text);
CREATE TABLE "month" (
	`id`	integer PRIMARY KEY AUTOINCREMENT,
	`name`	string,
	`color`	string
);
CREATE TABLE "img" (
	`id`	integer PRIMARY KEY AUTOINCREMENT,
	`title`	string,
	`day`	integer,
	`month`	integer,
	`user`	string NOT NULL,
	`slug`	string
);

insert into user values ("alexandersimoes@gmail.com", "pbkdf2:sha1:1000$OuZQGRws4zm$c985b1760876d09760978752c1c5a96ff1a05ed6");
insert into user values ("jnoelbasil@gmail.com", "pbkdf2:sha1:1000$OuZQGRws4zm$c985b1760876d09760978752c1c5a96ff1a05ed6");