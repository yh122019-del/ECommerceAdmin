class User:
    """用户类，用来保存用户的基本信息。"""

    def __init__(self, username, password, role="user"):
        # 用户名，用来登录系统
        self.username = username

        # 用户密码，Web 版本会保存加密后的哈希值
        self.password = password

        # 用户角色，user 表示普通用户，admin 表示管理员
        self.role = role

    def to_dict(self):
        """将用户对象转换成字典，方便保存到 JSON 文件。"""
        return {
            "username": self.username,
            "password": self.password,
            "role": self.role
        }
