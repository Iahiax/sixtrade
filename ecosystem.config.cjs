module.exports = {
  apps: [
    {
      name: 'finbert-bot',
      script: './venv/bin/python',
      args: 'bot.py',
      cwd: __dirname,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        PYTHONUNBUFFERED: '1',
      },
      error_file: './logs/bot-error.log',
      out_file: './logs/bot-out.log',
      time: true,
    },
    {
      name: 'finbert-web',
      script: 'npm',
      args: 'run dev',
      cwd: __dirname,
      autorestart: true,
      watch: false,
      max_memory_restart: '800M',
      env: {
        PORT: 3000,
        DISABLE_HMR: 'true',
      },
      error_file: './logs/web-error.log',
      out_file: './logs/web-out.log',
      time: true,
    },
  ],
};
