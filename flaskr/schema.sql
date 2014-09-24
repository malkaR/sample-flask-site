drop table if exists orders;
create table orders (
  id integer primary key,
  name varchar(120) not null,
  email varchar(120) null,
  state varchar(2)null,
  zipcode varchar(9) null,
  birthday date null,
  valid boolean default 1 not null,
  errors text null
);
