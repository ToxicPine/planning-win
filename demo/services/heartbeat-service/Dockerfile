FROM denoland/deno:2.2.5

# EXPOSE PORT_THAT_YOUR_APP_LISTENS_TO

WORKDIR /app

USER deno

RUN deno install
RUN deno cache main.ts

CMD ["run", "--allow-net", "--allow-env", "main.ts"]