drop table if exists orders;
create table orders (
  id integer primary key unique,
  name text not null,
  email text null,
  state text null,
  zipcode text null,
  birthday date null
);
