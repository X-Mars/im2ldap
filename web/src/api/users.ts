import request from './request'
import type { User } from './types'

export interface LoginResponse {
  access: string
  refresh: string
  user: User
}

export interface LoginParams {
  username: string
  password: string
}

export interface GitLabUser {
  id: string
  name: string
  username: string
  email: string
  avatar_url: string
  gitlab_id: string
  created_at: string
  updated_at: string
  linked?: boolean
  user_id?: string
}

export interface GiteeUser {
  id: string
  name: string
  username: string
  email: string
  avatar_url: string
  gitee_id: string
  created_at: string
  updated_at: string
  linked?: boolean
  user_id?: string
}

export interface WeComUser {
  id: string
  name: string
  username: string
  email: string
  mobile: string
  department: string
  position: string
  wecom_userid: string
  created_at: string
  updated_at: string
  avatar?: string
  linked?: boolean
  user_id?: string
}

export interface FeiShuUser {
  id: string
  name: string
  username: string
  email: string
  mobile: string
  department: string
  position: string
  feishu_userid: string
  created_at: string
  updated_at: string
  avatar?: string
  linked?: boolean
  user_id?: string
}

export interface DingTalkUser {
  id: string
  name: string
  username: string
  email: string
  mobile: string
  department: string
  position: string
  dingtalk_userid: string
  created_at: string
  updated_at: string
  avatar?: string
  linked?: boolean
  user_id?: string
}

export interface GitHubUser {
  id: string
  name: string
  username: string
  email: string
  avatar_url: string
  github_id: string
  created_at: string
  updated_at: string
  linked?: boolean
  user_id?: string
}

export interface GoogleUser {
  id: string
  name: string
  username: string
  email: string
  avatar_url: string
  google_id: string
  created_at: string
  updated_at: string
  linked?: boolean
  user_id?: string
}

export const userApi = {
  // 用户登录
  login: (data: LoginParams) => {
    return request.post<LoginResponse>('/auth/login/', data)
  },

  // 获取用户信息
  getUserInfo: () => {
    return request.get<User>('/auth/me/')
  },

  // 企业微信登录
  wecomLogin: (code: string) => {
    return request.post<LoginResponse>('/auth/wecom/login/', { code })
  },

  // 飞书登录
  feishuLogin: (code: string) => {
    return request.post<LoginResponse>('/auth/feishu/login/', { code })
  },

  // 钉钉登录
  dingtalkLogin: (authCode: string) => {
    return request.post<LoginResponse>('/auth/dingtalk/login/', { authCode })
  },

  // GitHub登录
  githubLogin: (code: string) => {
    return request.post<LoginResponse>('/auth/github/login/', { code })
  },

  // Google登录
  googleLogin: (code: string) => {
    return request.post<LoginResponse>('/auth/google/login/', { code })
  },

  // GitLab登录
  gitlabLogin: (code: string) => {
    return request.post<LoginResponse>('/auth/gitlab/login/', { code })
  },

  // Gitee登录
  giteeLogin: (code: string) => {
    return request.post<LoginResponse>('/auth/gitee/login/', { code })
  },

  // 获取第三方登录二维码
  getLoginQRCode: () => {
    return request.get<{
      wecom_url: string | null
      feishu_url: string | null
      dingtalk_url: string | null
      github_url: string | null
      google_url: string | null
      gitlab_url: string | null
      gitee_url: string | null
    }>('/auth/login/qrcode/')
  },

  // 获取本地用户列表
  getUsers: () => {
    return request.get<User[]>('/auth/users/')
  },

  // 创建本地用户
  createUser: (data: Partial<User>) => {
    return request.post<User>('/auth/users/', data)
  },

  // 更新本地用户
  updateUser: (id: string, data: Partial<User>) => {
    return request.patch<User>(`/auth/users/${id}/`, data)
  },

  // 删除本地用户
  deleteUser: (id: string) => {
    return request.delete(`/auth/users/${id}/`)
  },

  // 获取企业微信用户列表
  getWeComUsers: () => {
    return request.get<WeComUser[]>('/auth/wecom-users/')
  },

  // 获取飞书用户列表
  getFeiShuUsers: () => {
    return request.get<FeiShuUser[]>('/auth/feishu-users/')
  },

  // 获取钉钉用户列表
  getDingTalkUsers: () => {
    return request.get<DingTalkUser[]>('/auth/dingtalk-users/')
  },

  // 获取GitHub用户列表
  getGitHubUsers: () => {
    return request.get<GitHubUser[]>('/auth/github-users/')
  },

  // 获取Google用户列表
  getGoogleUsers: () => {
    return request.get<GoogleUser[]>('/auth/google-users/')
  },

  // 获取GitLab用户列表
  getGitLabUsers: () => {
    return request.get<GitLabUser[]>('/auth/gitlab-users/')
  },

  // 获取Gitee用户列表
  getGiteeUsers: () => {
    return request.get<GiteeUser[]>('/auth/gitee-users/')
  },

  // 链接本地用户和第三方用户
  linkUser: (localUserId: string, thirdPartyUserId: string, thirdPartyType: string) => {
    return request({
      url: '/auth/link-user/',
      method: 'post',
      data: {
        local_user_id: localUserId,
        third_party_user_id: thirdPartyUserId,
        third_party_type: thirdPartyType
      }
    });
  },

  // 解除本地用户和第三方用户的链接
  unlinkUser: (userId: string, thirdPartyType: string) => {
    return request.post(`/auth/users/${userId}/unlink/`, {
      third_party_type: thirdPartyType
    })
  }
}
