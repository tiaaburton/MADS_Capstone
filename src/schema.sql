DROP TABLE IF EXISTS user;

-- CREATE TABLE user (
--   id INTEGER PRIMARY KEY AUTOINCREMENT,
--   username TEXT UNIQUE NOT NULL,
--   password TEXT NOT NULL
-- );

CREATE TABLE user (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  profile_pic TEXT NOT NULL
);