drop table if exists hosts;
create table hosts(
	id integer primary key autoincrement,
	host text not null,
	port integer not null
);
insert into hosts(host,port) values('localhost',2375);