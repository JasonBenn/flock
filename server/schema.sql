DROP TABLE IF EXISTS device;
DROP TABLE IF EXISTS post;

-- first name, last name,

CREATE TABLE device (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  hostname TEXT UNIQUE NOT NULL,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL
);
