const API_BASE_URL =
  "http://localhost:5000/api";

interface ApiOptions {
  method?: string;
  headers?: HeadersInit;
  body?: unknown;
}

class ApiClient {
  private getToken(): string | null {
    return localStorage.getItem(
      "authToken"
    );
  }

  async request<T>(
    endpoint: string,
    options: ApiOptions = {}
  ): Promise<T> {
    const token =
      this.getToken();

    const headers: Record<
      string,
      string
    > = {
      "Content-Type":
        "application/json",
    };

    if (options.headers) {
      const existingHeaders =
        new Headers(
          options.headers
        );

      existingHeaders.forEach(
        (value, key) => {
          headers[key] = value;
        }
      );
    }

    if (token) {
      headers.Authorization =
        `Bearer ${token}`;
    }

    const response =
      await fetch(
        `${API_BASE_URL}${endpoint}`,
        {
          method:
            options.method || "GET",

          headers,

          body:
            options.body !== undefined
              ? JSON.stringify(
                  options.body
                )
              : undefined,
        }
      );

    let result: unknown = null;

    try {
      result =
        await response.json();
    } catch {
      result = null;
    }

    if (!response.ok) {
      const errorResult =
        result as {
          message?: string;
        } | null;

      throw new Error(
        errorResult?.message ||
          `Request failed with status ${response.status}`
      );
    }

    return result as T;
  }

  get<T>(
    endpoint: string
  ): Promise<T> {
    return this.request<T>(
      endpoint,
      {
        method: "GET",
      }
    );
  }

  post<T>(
    endpoint: string,
    body?: unknown
  ): Promise<T> {
    return this.request<T>(
      endpoint,
      {
        method: "POST",
        body,
      }
    );
  }

  put<T>(
    endpoint: string,
    body?: unknown
  ): Promise<T> {
    return this.request<T>(
      endpoint,
      {
        method: "PUT",
        body,
      }
    );
  }

  patch<T>(
    endpoint: string,
    body?: unknown
  ): Promise<T> {
    return this.request<T>(
      endpoint,
      {
        method: "PATCH",
        body,
      }
    );
  }

  delete<T>(
    endpoint: string
  ): Promise<T> {
    return this.request<T>(
      endpoint,
      {
        method: "DELETE",
      }
    );
  }
}

export const apiClient =
  new ApiClient();