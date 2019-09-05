DROP TABLE IF EXISTS device;
DROP TABLE IF EXISTS post;

-- first name, last name,

CREATE TABLE device (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  mac TEXT UNIQUE NOT NULL,
  FOREIGN KEY(person_id) REFERENCES person(id)
);
