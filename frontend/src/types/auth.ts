export type User = {
  id: number;
  email: string;
  name: string;
  allow_training_data_collection?: boolean;
  created_at: string;
  updated_at: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
  user: User;
};

export type AuthError = {
  error: {
    code: string;
    message: string;
    details?: string[];
  };
};
