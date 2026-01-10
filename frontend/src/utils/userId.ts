const USER_ID_KEY = 'predictous_user_id';

export function getUserId(): string {
  let userId = localStorage.getItem(USER_ID_KEY);
  if (!userId) {
    userId = crypto.randomUUID?.() ?? Math.random().toString(36).slice(2);
    localStorage.setItem(USER_ID_KEY, userId);
  }
  return userId;
}
