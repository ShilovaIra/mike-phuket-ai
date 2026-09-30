function displayName(user) {
  if (!user) return "Гость";
  if (!user.last_name) return user.first_name;
  return user.first_name + " " + user.last_name;
}

export function profileView(user) {
  const name = displayName(user);
  return {
    name,
    letter: Array.from(name)[0],
    photoUrl: user && user.photo_url ? user.photo_url : null,
  };
}
