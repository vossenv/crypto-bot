
$v = 1.8

docker system prune -a -f
docker build --tag=crypto-bot . --no-cache
$x = -split (docker image ls)
docker tag $x[8] vossenv/crypto-bot:$v
docker push vossenv/crypto-bot:$v