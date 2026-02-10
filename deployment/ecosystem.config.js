module.exports = {
    apps: [
        {
            name: "invoice-frontend",
            cwd: "/home/harvad/invoice-processor/frontend",
            script: "npm",
            args: "start",
            env: {
                NODE_ENV: "production",
                PORT: 3009
            }
        }
    ]
};
