Before running:

``` bash
sudo sysctl kernel.perf_event_paranoid=3
perf stat -e cycles ls
```
