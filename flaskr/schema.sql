drop table if exists orders;
create table orders (
  id integer primary key,
  name text not null,
  email text null,
  state text null,
  zipcode integer null,
  birthday date null
);
