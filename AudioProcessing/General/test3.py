def live():
        global running
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        while True:
                target_ip = "35.186.188.127"
                target_port = 10000
                s.connect((target_ip, target_port))
                break

        CHUNK = 4096 # 512
        audio_format = pyaudio.paInt16
        channels = 1
        RATE = 44100 
        cRATE = 22050 

        print("Connected to Server") 
 
        fm, f0, f1, f2, f3 = [], [], [], [], [] 
        n = 25 
         
        global ind 
        ind = 0 
        i = 0 
        data = np.array([]) 
 
        threading.Thread(target=live_classification,args=(model,device,classes, CHUNK, n), daemon=True).start() 
        threading.Thread(target=live_classification,args=(model,device,classes, CHUNK, n), daemon=True).start() 
        threading.Thread(target=live_classification,args=(model,device,classes, CHUNK, n), daemon=True).start() 
        #threading.Thread(target=live_classification,args=(model,device,classes, CHUNK, n)).start() 
        #threading.Thread(target=live_classification,args=(model,device,classes, CHUNK, n)).start() 
        #threading.Thread(target=live_classification,args=(model,device,classes, CHUNK, n)).start() 
        #threading.Thread(target=live_classification,args=(model,device,classes, CHUNK, n)).start() 
 
        s.settimeout(5) 
 
        while running: 
                try: 
                        d = s.recv(CHUNK)

                        c0 = channels[0::8].tobytes() #red
                        c1 = channels[1::8].tobytes() #green
                        c2 = channels[2::8].tobytes() #blue
                        c3 = channels[3::8].tobytes() #purple

                        if not d: break
                        data = np.concatenate([data, np.frombuffer(d, dtype=np.int16)])
                                #threading.Thread(target=live_classification,args=(model,device,classes, CHUNK, n)).start()
                        channels = np.frombuffer(data, dtype='float32')

                        fm.append(data)
                        # f0.append(c0.tobytes())
                        # f1.append(c1.tobytes())
                        # f2.append(c2.tobytes())
                        # f3.append(c3.tobytes())

                        # f3[-1]
                        if i % n == 0 and i != 0:
                                ind +=1
                                queue.append(data)
                                data = np.array([])
                                #queue.append([])
                                sprint("len", len(queue))
                        i+=1

                except socket.timeout:
                        print('lag')
                        s.close()
                except KeyboardInterrupt as e:
                        print("Client Disconnected")
                        s.close()