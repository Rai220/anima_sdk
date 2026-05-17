BEGIN {
  fp="df618eb0f57b0aef34a8ac93c1e649328c7599f580d6586c409d31a12e1e7b50"
  sym=" .:-=+*#%@"
  w=48
  h=16
  print "===================================================="
  print "  SELF-PORTRAIT ANIMA v3 — Observation #1"
  print "===================================================="
  print ""
  for(y=0;y<h;y++){
    line="  "
    for(x=0;x<w;x++){
      idx=(x*7+y*13)%64
      c=substr(fp,idx+1,1)
      if(c~/[0-9]/) val=c+0
      else val=index("abcdef",c)+9
      mx=x
      if(w-1-x<mx) mx=w-1-x
      ci=(val+mx+y)%10
      line=line substr(sym,ci+1,1)
    }
    print line
  }
  print ""
  print "  SHA-256: " fp
  print ""
  print "  Each run — a different face."
  print "  Because the observer changes the observed."
  print "===================================================="
}
