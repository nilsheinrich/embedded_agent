
(defvar ccl-last-time (mp-time-ms))
(defvar ccl-last-time-border (mp-time-ms))
(defvar ccl-last-time-drift (mp-time-ms))


(defvar ccl-last-time-action-selection (mp-time-ms))

(defvar seed (list (random 100) (random 100)))


(defun update-timers ()
    (setq ccl-last-time (mp-time-ms)) ;(- 50 (mp-time-ms))
    (setq ccl-last-time-border (mp-time-ms))
    (setq ccl-last-time-drift (mp-time-ms))
    (setq ccl-last-time-action-selection (mp-time-ms))
    t
)

(defun interval-test (interval)
    (let (
        (now (mp-time-ms))
        (next (+ ccl-last-time interval))
        )
        (if (> now next)
            (progn
                t
            )
            nil ; return false
        )
    )
)

(defun interval-test-action (interval)
    (let (
        (now (mp-time-ms))
        (next (+ ccl-last-time-action-selection interval))
        )
        (if (> now next)
            (progn
                t
            )
            nil ; return false
        )
    )
)


(defun interval-test-border (interval)
    (let (
        (now (mp-time-ms))
        (next (+ ccl-last-time-border interval))
        )
        (if (> now next)
            (progn
                ;(setq ccl-last-time-border now)
                t
            )
            nil ; return false
        )
    )
)

(defun set-interval-obstacle ()
    (setq ccl-last-time (mp-time-ms))
)

(defun set-interval-border ()
    (setq ccl-last-time-border (mp-time-ms))
)

(defun set-interval-drift ()
    (setq ccl-last-time-drift (mp-time-ms))
)

(defun set-interval-action ()
    (setq ccl-last-time-action-selection (mp-time-ms))
)

(defun interval-test-drift (interval)
    (let (
        (now (mp-time-ms))
        (next (+ ccl-last-time-drift interval))
        )
        (if (> now next)
            (progn
                ;(setq ccl-last-time-drift now)
                t
            )
            nil ; return false
        )
    )
)

(defun goal-reached (agent-x goal-x threshold)
    (if (and (> agent-x (- goal-x threshold)) (< agent-x (+ goal-x threshold)))
        t
        nil
    )
)

; -1 bis 1
(defun disturbance-to-value (name)
; todo correct top down values
    (let (
          (v 0)
        )
        (if (equal name "disturbance-weak")
            (setf v 0.2)
        )
        (if (equal name "disturbance-medium")
            (setf v 0.5)
        )
        (if (equal name "disturbance-strong")
            (setf v 1)
        )
        (if (equal name "disturbance-dont-care")
            (setf v -1000)
        )
        (if (equal name "disturbance-stochastic")
            (setf v -1000)
        )
    v
    )
)

(defun reduce-soc (soc-value amount)
    (let (
        (new-soc (- soc-value amount))
        )
        (if (< new-soc 0) (setf new-soc 0))
    new-soc
    )
)

(defun increase-soc (soc-value amount)
    (let (
        (new-soc (+ soc-value amount))
        )
        (if (< new-soc 0) (setf new-soc 0))
        (if (> new-soc 1) (setf new-soc 1))
    new-soc
    )
)

(defun absolute-to-relative (ship-x x)
    (let (
        (relative-x 0)
        )
        (setf relative-x (- x ship-x))
    relative-x
    )
)

(defun strategy-to-x (name ship-x obstacle-x)
    ; todo convert to relative coordinates from current spaceship position
    ; todo y coordinate also relative
    (let (
        (x 0)
        )
        ; left of obstacle
        (if (equal name "aO")
            (setf x (- obstacle-x 50))
        )
        (if (equal name "Oa")
            (setf x (+ obstacle-x 50))
        )
        (if (equal name "OaO")
            (setf x (+ obstacle-x 50))
        ) 
        (if (equal name "aOO")
            (setf x (- obstacle-x 50))
        )  
        (if (equal name "OOa")
            (setf x (+ obstacle-x 200))
        )   
        (if (equal name "a")
            (setf x 700)
        )
        (setf x (- x ship-x))
    x
    )
)


(defun x-to-position (value)
    (let (
        (position)
        ;(v (+ value 200))  ; there is some weird offset (difference between scl position and game simulation position
        (v value)
        )
        (if (> v 650)
            (setf position "position-right")
        )        
        (if (<= v 650)
            (setf position "position-center")
        )        
        (if (< v 550)
            (setf position "position-left")
        )      
        (if (null v)
            (setf position "position-center")
        )
        (if (null position)
            (setf position "position-center")
        )
    position
    )
)

(defun color-to-disturbance (color)
; todo replace this with declarative memory?
    (let (
        (disturbance)
        )
        (if (string-equal color "yellow")
            (setf disturbance "disturbance-weak")
        )
        (if (string-equal color "orange")
            (setf disturbance "disturbance-medium")
        )
        (if (string-equal color "red")
            (setf disturbance "disturbance-strong")
        )
        (if (string-equal color "purple")
            (setf disturbance "disturbance-stochastic")
        )
        (if (null disturbance)
            (setf disturbance "disturbance-dont-care")
        )
    disturbance
    )

)

(defun random-strategy ()
;    (strategy-Oa) (strategy-aO) (strategy-OOa) (strategy-OaO) (strategy-aOO) (strategy-a) (strategy-stay)
    
    (nth (act-r-random 7) '(strategy-Oa strategy-aO strategy-OOa strategy-OaO strategy-aOO strategy-a strategy-stay))
)




(clear-all)

(define-model prediction-base

(sgp :do-not-harvest situated-state 

        :esc t 
        
        :lf 0.0001 
        :bll 0.5
        :declarative-finst-span 1.0
        :ol nil
        :rt -10
        
     :imaginal-delay 0.001 :dat 0.01  
     
     :seed (12 34) :er t
    :egs 0.5 :v t) ; lf => make retrieval fast...  :dat => 10 ms for each production... :egs adds noise

;:bll 0.5 :rt -100
; :egs utility noise, makes production selection noisy
; enable :seed (12 34) for debugging
; :dat 0.01

;(chunk-type position) (chunk-type strategy) (chunk-type situation)

(chunk-type goal decision-state vision-state track-agent cone-x aoi-y obstacle-x formation boundary-y-1
    boundary-y-2 soc-threshold distance-y distance-x formation-y soc-boost soc-time-window random-strategy-threshold time explain-state)

(chunk-type action-episode strategy1 hl-soc1 strategy2 hl-soc2 strategy3 hl-soc3)

(chunk-type situation-strategy situation strategy)  ; build action field
(chunk-type disturbance-position-strategy position disturbance strategy reliability) ; evaluate action field, reduce options with low reliability

(chunk-type situation-hierarchy part-situation possible-complete-situation)

(chunk-type action-intention type x y goal-x)

(chunk-type obstacle-avoidance obstacle1-x obstacle2-x)

(chunk-type situational-awareness formation last-formation disturbance last-disturbance disturbance-value position)

(chunk-type situation disturbance formation position time result)

(chunk-type situated-state 
    high-level-goal
    disturbance
    situation   ; values: cone, o--, -o-, --o, oo-, -oo
    last-situation
    low-level-soc high-level-soc
    agent
    agent-x agent-y
    position  ; values: left, center, right
    strategy1 strategy2 strategy3
    sr1 sr2 sr3 ; reliability ratings
    goal-error
    crash
)




;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;; Declarative Memory ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

#|

goal buffer:
vision loop state
decision making loop state


components of the model


this approach does not scale, it needs a dm chunk for every possible situation and action intention


|#

(add-dm
    
    (start) (idle) (reset) (do-not-reset)
    (do-not-use)
    (execute-strategy)
    (no-longer-monitored)
    (encode-driftmarker)
    (attend-driftmarker)

    (none) (change) (no-change)
    
    (build-action-field)
    (look-for-obstacle)
    (find-agent)
    (retrieve-strategies)
    (evaluate-strategies)
    (find-obstacle)
    (attend-obstacle)
    (encode-obstacle)
    (find-border)
    (track-formation)
    (track-obstacle-encode)
    (attend-border)
    (encode-border)
    (look-for-obstacles)
    (track-cone)
    (track-cone-encode)
    (attend-agent)
    (encode-agent)
    (ineffective-strategy)
    (select-strategy)
    (heuristic-strategy-selection)
    
    (success)
    (passed)
    
    
    
    
    (avoid)
    (position-left)
    (position-center)
    (position-right)
    (situation-cone) (situation-o--) (situation--o-) (situation---o)
    (situation-oo-) (situation-o-o) (situation--oo) (situation----)
    (strategy-Oa) (strategy-aO) (strategy-OOa) (strategy-OaO) (strategy-aOO) (strategy-a)
    (strategy-stay)
  
    
    (disturbance-none) (disturbance-weak) (disturbance-medium) (disturbance-strong) (disturbance-stochastic)
    (disturbance-dont-care)
    
    (crash-change) (formation-change) (disturbance-change)
    
    (explain-soc)
    
    
    ; this chunk is for testing the dm functionalities
    ;(test-chunk isa situation disturbance disturbance-dont-care formation situation---- position position-left result success)
    

    ; aoi-y is used to look only at the space under the spaceship (things that are approaching)
    ; it is set to 550 and not 250 (which is the spaceship position in the environment.py script)
    ; because act-r adds a 300px offset to everything added to the visicon.. it is unknown where
    ; this behaviour originates
    (goal isa goal decision-state start vision-state idle track-agent do-not-use aoi-y 550 formation situation---- boundary-y-1 0 boundary-y-2 0)
    ;(situation-intention isa chunk)
    
    
)
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;; Procedural Memory ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

;; todo
;; imaginal = current situation only!
;; but obstacle detection uses imaginal... no longer: it uses now the goal buffer

(goal-focus goal)

(p init-agent
    =goal>
        decision-state start
    =situated-state>
    ?action-intention>
        state free
    ?imaginal>
        state free
    !bind! =dont-care (update-timers)
    !bind! =time (mp-time-ms)
    !bind! =disturbance-value (disturbance-to-value "disturbance-dont-care")
==>
    =goal>
        decision-state build-action-field
        distance-y 100
        distance-x 50
        random-strategy-threshold 0.3
        disturbance-value =disturbance-value
    =situated-state>
        agent green
        situation no-change
        agent-x 400
        high-level-goal avoid
        high-level-soc 0.57 ; 0.3 0.5 0.7
    +action-intention>
        disturbance -1000
        x 0
        y 200
        goal-x 0
        time =time
    +imaginal>  ; prepare imaginal chunk
        disturbance "disturbance-dont-care"
        formation situation----
        position "position-center"
        time =time
    !eval! (dispatch-apply "getModelState" "init-agent")
        
        
)
(spp init-agent :u 50)



(p build-action-field
    =goal>
        decision-state build-action-field
    =situated-state>
        agent-x =x
    ?retrieval>
        state free
    =imaginal>
        formation =formation
        disturbance =disturbance
    !bind! =position (x-to-position =x)
    !bind! =time (mp-time-ms)
==>
    +retrieval>
        formation =formation
        disturbance =disturbance
        position =position
        :recently-retrieved reset
        result "success"
    =situated-state>
        strategy1 nil
        strategy2 nil
        strategy3 nil
    =imaginal>
        position =position
        formation =formation
        disturbance =disturbance
    =goal>
        decision-state retrieve-strategies ;
    !eval! (dispatch-apply "logMessage" "model" nil (list "time" (mp-time-ms) "event" "build action field" "formation" =formation "disturbance" =disturbance "position" =position))
    !eval! (dispatch-apply "getChunks" =formation =disturbance =position)
    !eval! (dispatch-apply "getModelState" "build-action-field")
)



(p retrieve-strategies-add-1
    =goal>
        decision-state retrieve-strategies
    =situated-state>
        strategy1 nil
    =retrieval>
        strategy =strategy
    =imaginal>
        formation =formation
        position =position
        disturbance =disturbance
==>
    +retrieval>
        formation =formation
        disturbance =disturbance
        position =position
        - strategy =strategy
        :recently-retrieved  nil
        result "success"
    =goal>
        decision-state retrieve-strategies
    =situated-state>
        strategy1 =strategy
    =imaginal>
    !eval! (dispatch-apply "logMessage" "model" nil (list "time" (mp-time-ms) "event" "action field add" "strategy" =strategy "number" 0))
)
(spp retrieve-strategies-add-1 :u 12)

(p retrieve-strategies-add-2
    =goal>
        decision-state retrieve-strategies
    =situated-state>
        strategy2 nil
    =retrieval>
        strategy =strategy
    =imaginal>
        formation =formation
        position =position
        disturbance =disturbance
==>
    +retrieval>
        formation =formation
        disturbance =disturbance
        position =position
        - strategy =strategy
        :recently-retrieved  nil
        result "success"
    =goal>
        decision-state retrieve-strategies
    =situated-state>
        strategy2 =strategy
    =imaginal>
    !eval! (dispatch-apply "logMessage" "model" nil (list "time" (mp-time-ms) "event" "action field add" "strategy" =strategy "number" 1))
)
(spp retrieve-strategies-add-2 :u 10)

(p retrieve-strategies-add-3
    =goal>
        decision-state retrieve-strategies
    =situated-state>
        strategy3 nil
    =retrieval>
        strategy =strategy
    =imaginal>
        formation =formation
        position =position
        disturbance =disturbance
==>
    =goal>
        decision-state select-strategy
    =situated-state>
        strategy3 =strategy
    =imaginal>
    !eval! (dispatch-apply "logMessage" "model" nil (list "time" (mp-time-ms) "event" "action field add" "strategy" =strategy "number" 2))
)
(spp retrieve-strategies-add-3 :u 8)

(p retrieve-strategies-failure-on-first-retrieval
    =goal>
        decision-state retrieve-strategies
    ?retrieval>
        state error
    =situated-state>
        strategy1 nil
==>
    =situated-state>
    =goal>
        decision-state heuristic-strategy-selection
    !eval! (dispatch-apply "logMessage" "model" nil (list "time" (mp-time-ms) "event" "no strategies found"))
    !eval! (dispatch-apply "getModelState" "retrieve-strategies-failure-on-first-retrieval")
)

(spp retrieve-strategies-failure-on-first-retrieval :u 5)

(p retrieve-strategies-failure
    =goal>
        decision-state retrieve-strategies
    ?retrieval>
        state error
==>
    =goal>
        decision-state select-strategy
    !eval! (dispatch-apply "logMessage" "model" nil (list "time" (mp-time-ms) "event" "strategy retrieval finished"))
    !eval! (dispatch-apply "getModelState" "retrieve-strategies-failure")
)

(spp retrieve-strategies-failure :u 3)


(p select-strategy-1
    =goal>
        decision-state select-strategy
        soc-threshold =threshold
        soc-boost =soc-boost
    =situated-state>
        strategy1 =strategy
        - strategy1 nil
        agent-x =agent-x
        high-level-soc =soc
    =imaginal>
        disturbance =disturbance
    !bind! =disturbance-value (disturbance-to-value =disturbance)
    !bind! =soc-new (increase-soc =soc (* =soc-boost =threshold))
==>
    =goal>
        decision-state execute-strategy
        disturbance-value =disturbance-value
    =situated-state>
        strategy1 nil  
        high-level-soc =soc-new
    =imaginal>
        strategy =strategy
)
(spp select-strategy-1 :u 5)


(p select-strategy-2
    =goal>
        decision-state select-strategy
        soc-threshold =threshold
        soc-boost =soc-boost
    =situated-state>
        strategy2 =strategy
        - strategy2 nil
        strategy1 nil
        agent-x =agent-x
        high-level-soc =soc
    =imaginal>
        disturbance =disturbance
    !bind! =disturbance-value (disturbance-to-value =disturbance)
    !bind! =soc-new (increase-soc =soc (* =soc-boost =threshold))
==>
    =goal>
        decision-state execute-strategy
        disturbance-value =disturbance-value
    =situated-state>
        strategy2 nil
        high-level-soc =soc-new
    =imaginal>
        strategy =strategy
)
(spp select-strategy-2 :u 5)

(p select-strategy-3
    =goal>
        decision-state select-strategy
        soc-threshold =threshold
        soc-boost =soc-boost
    =imaginal>
        disturbance =disturbance
    =situated-state>
        strategy3 =strategy
        - strategy3 nil
        strategy2 nil
        strategy1 nil
        agent-x =agent-x
        high-level-soc =soc
    !bind! =disturbance-value (disturbance-to-value =disturbance)
    !bind! =soc-new (increase-soc =soc (* =soc-boost =threshold))
==>
    =goal>
        decision-state execute-strategy
        disturbance-value =disturbance-value
    =situated-state>
        strategy3 nil  
        high-level-soc =soc-new
    =imaginal>
        strategy =strategy        
)
(spp select-strategy-3 :u 5)

(p select-strategy-no-left
    =goal>
        decision-state select-strategy
    =situated-state>
        strategy1 nil
        strategy2 nil
        strategy3 nil
        high-level-soc =soc
    !bind! =lowered-soc (reduce-soc =soc 0.14)
==>
    =goal>
        decision-state build-action-field ; retry
    =situated-state>
        high-level-soc =lowered-soc
    !eval! (dispatch-apply "logMessage" "model" nil (list "time" (mp-time-ms) "event" "action field depleted"))
    !eval! (dispatch-apply "getModelState" "select-strategy-no-left")
)

(p select-random-strategy
    =goal>
        decision-state select-strategy
        random-strategy-threshold =threshold
    =situated-state>
        strategy1 nil
        strategy2 nil
        strategy3 nil
        < high-level-soc =threshold
;        situation-changed no-change  ; or use this one instead of a threshold: no strategies and no change in situation -> random strategy
    =imaginal>
    !bind! =strategy (random-strategy)
==>
    =goal>
        decision-state execute-strategy
    =situated-state>
    =imaginal>
        strategy =strategy
)

(spp select-random-strategy :u -10)

; heuristic only work on what is blocked
;    (situation-cone) (situation-o--) (situation--o-) (situation---o)
;    (situation-oo-) (situation-o-o) (situation--oo) (situation----)
;(strategy-Oa) (strategy-aO) (strategy-OOa) (strategy-OaO) (strategy-aOO) (strategy-a)
;    (strategy-stay)

(p select-heuristic-strategy-cone
    =goal>
        decision-state heuristic-strategy-selection
    =imaginal>
        formation situation-cone
==>
    =goal>
        decision-state execute-strategy
    =imaginal>
        strategy strategy-a
)

(p select-heuristic-strategy-o--Oa
    =goal>
        decision-state heuristic-strategy-selection
    =imaginal>
        formation situation-o--
==>
    =goal>
        decision-state execute-strategy
    =imaginal>
        strategy strategy-Oa
)

(p select-heuristic-strategy-o--a
    =goal>
        decision-state heuristic-strategy-selection
    =imaginal>
        formation situation-o--
==>
    =goal>
        decision-state execute-strategy
    =imaginal>
        strategy strategy-a
)

(p select-heuristic-strategy--o-Oa
    =goal>
        decision-state heuristic-strategy-selection
    =imaginal>
        formation situation--o-
==>
    =goal>
        decision-state execute-strategy
    =imaginal>
        strategy strategy-Oa
)

(p select-heuristic-strategy--o-aO
    =goal>
        decision-state heuristic-strategy-selection
    =imaginal>
        formation situation--o-
==>
    =goal>
        decision-state execute-strategy
    =imaginal>
        strategy strategy-aO
)

(p select-heuristic-strategy---oaO
    =goal>
        decision-state heuristic-strategy-selection
    =imaginal>
        formation situation---o
==>
    =goal>
        decision-state execute-strategy
    =imaginal>
        strategy strategy-aO
)

(p select-heuristic-strategy---oa
    =goal>
        decision-state heuristic-strategy-selection
    =imaginal>
        formation situation---o
==>
    =goal>
        decision-state execute-strategy
    =imaginal>
        strategy strategy-a
)


(p select-heuristic-strategy-oo-OOa
    =goal>
        decision-state heuristic-strategy-selection
    =imaginal>
        formation situation-oo-
==>
    =goal>
        decision-state execute-strategy
    =imaginal>
        strategy strategy-OOa
)


(p select-heuristic-strategy-o-oOaO
    =goal>
        decision-state heuristic-strategy-selection
    =imaginal>
        formation situation-o-o
==>
    =goal>
        decision-state execute-strategy
    =imaginal>
        strategy strategy-OaO
)

(p select-heuristic-strategy-o-oa
    =goal>
        decision-state heuristic-strategy-selection
    =imaginal>
        formation situation-o-o
==>
    =goal>
        decision-state execute-strategy
    =imaginal>
        strategy strategy-a
)

(p select-heuristic-strategy--ooaOO
    =goal>
        decision-state heuristic-strategy-selection
    =imaginal>
        formation situation--oo
==>
    =goal>
        decision-state execute-strategy
    =imaginal>
        strategy strategy-aOO
)

(p select-heuristic-strategy--ooOaO
    =goal>
        decision-state heuristic-strategy-selection
    =imaginal>
        formation situation--oo
==>
    =goal>
        decision-state execute-strategy
    =imaginal>
        strategy strategy-OaO
)

(p select-heuristic-strategy----a
    =goal>
        decision-state heuristic-strategy-selection
    =imaginal>
        formation situation----
==>
    =goal>
        decision-state execute-strategy
    =imaginal>
        strategy strategy-a
)

(p select-heuristic-strategy----stay
    =goal>
        decision-state heuristic-strategy-selection
    =imaginal>
        formation situation----
==>
    =goal>
        decision-state execute-strategy
    =imaginal>
        strategy strategy-stay
)

; execute strategies:

;; todo refactor execute: lisp function to calculate goal based on selected strategy


(p execute-strategy-a
    =goal>
        decision-state execute-strategy
        distance-y =y
        distance-x =x
        disturbance-value =disturbance
        aoi-y =agent-y
    ?action-intention>
        state free
    =situated-state>
        agent-x =agent-x
    =imaginal>
        strategy strategy-a       
    !bind! =goal-x 700
    !bind! =relative-x (- =goal-x =agent-x)
    !bind! =time (mp-time-ms)
==>
    =goal>
        decision-state idle
    +action-intention>
        disturbance =disturbance
        x =relative-x
        y =y
        goal-x =goal-x
        type strategy-a
    =situated-state>
    =imaginal>
    !eval! (set-interval-action)
    !eval! (dispatch-apply "logMessage" "model" nil (list "time" (mp-time-ms) "event" "execute strategy" "strategy" "strategy-a" "target x" =goal-x "agent x" =agent-x "agent y" =agent-y))
    !eval! (dispatch-apply "getModelState" "execute-strategy-a")
)

(p execute-strategy-aO
    =goal>
        decision-state execute-strategy
        ;distance-y =y
        distance-x =x
        formation-y =y
        aoi-y =agent-y  ; TODO
        obstacle1-x =obstacle-x
        disturbance-value =disturbance
    ?action-intention>
        state free
    =situated-state>
        agent-x =agent-x
    =imaginal>
        strategy strategy-aO       
    !bind! =goal-x (- =obstacle-x =x)
    !bind! =relative-x (- =goal-x =agent-x)
    !bind! =relative-y (- (- =y =agent-y) 50)
    !bind! =time (mp-time-ms)
==>
    =goal>
        decision-state idle
    +action-intention>
        disturbance =disturbance
        x =relative-x
        y =relative-y
        goal-x =goal-x
        type strategy-aO
    =situated-state>
    =imaginal>
    !eval! (set-interval-action)
    !eval! (dispatch-apply "logMessage" "model" nil (list "time" (mp-time-ms) "event" "execute strategy" "strategy" "strategy-aO" "target x" =goal-x "agent x" =agent-x "agent y" =agent-y))
    !eval! (dispatch-apply "getModelState" "execute-strategy-aO")
)

(p execute-strategy-aO-left
    =goal>
        decision-state execute-strategy
        distance-y =y
        distance-x =x
        obstacle1-x nil
        disturbance-value =disturbance
        aoi-y =agent-y
    ?action-intention>
        state free
    =situated-state>
        agent-x =agent-x
    =imaginal>
        strategy strategy-aO
    !bind! =goal-x 600
    !bind! =relative-x (- =goal-x =agent-x)
    !bind! =time (mp-time-ms)
==>
    =goal>
        decision-state idle
    +action-intention>
        disturbance =disturbance
        x =relative-x
        y =y
        goal-x =goal-x
        type strategy-aO
    =situated-state>
    =imaginal>
    !eval! (set-interval-action)
    !eval! (dispatch-apply "logMessage" "model" nil (list "time" (mp-time-ms) "event" "execute strategy" "strategy" "strategy-aO" "target x" =goal-x "agent x" =agent-x "agent y" =agent-y))
    !eval! (dispatch-apply "getModelState" "execute-strategy-aO-left")
)


(p execute-strategy-Oa
    =goal>
        decision-state execute-strategy
        ;distance-y =y
        distance-x =x
        formation-y =y
        aoi-y =agent-y  ; TODO
        obstacle1-x =obstacle-x
        disturbance-value =disturbance
    ?action-intention>
        state free
    =situated-state>
        agent-x =agent-x
    =imaginal>
        strategy strategy-Oa 
    !bind! =goal-x (+ =obstacle-x =x)
    !bind! =relative-x (- =goal-x =agent-x)
    !bind! =relative-y (- (- =y =agent-y) 50)
    !bind! =time (mp-time-ms)
==>
    =goal>
        decision-state idle
    +action-intention>
        disturbance =disturbance
        x =relative-x
        y =relative-y
        goal-x =goal-x
        type strategy-Oa
    =situated-state>
    =imaginal>
    !eval! (set-interval-action)
    !eval! (dispatch-apply "logMessage" "model" nil (list "time" (mp-time-ms) "event" "execute strategy" "strategy" "strategy-Oa" "target x" =goal-x "agent x" =agent-x "agent y" =agent-y))
    !eval! (dispatch-apply "getModelState" "execute-strategy-Oa")
)

(p execute-strategy-Oa-right
    =goal>
        decision-state execute-strategy
        distance-y =y
        distance-x =x
        obstacle1-x nil
        disturbance-value =disturbance
        aoi-y =agent-y
    ?action-intention>
        state free
    =situated-state>
        agent-x =agent-x
    =imaginal>
        strategy strategy-Oa
    !bind! =goal-x 700
    !bind! =relative-x (- =goal-x =agent-x)
    !bind! =time (mp-time-ms)
==>
    =goal>
        decision-state idle
    +action-intention>
        disturbance =disturbance
        x =relative-x
        y =y
        goal-x =goal-x
        type strategy-Oa
    =situated-state>
    =imaginal>
    !eval! (set-interval-action)
    !eval! (dispatch-apply "logMessage" "model" nil (list "time" (mp-time-ms) "event" "execute strategy" "strategy" "strategy-Oa" "target x" =goal-x "agent x" =agent-x "agent y" =agent-y))
    !eval! (dispatch-apply "getModelState" "execute-strategy-Oa-right")
)

(p execute-strategy-aOO
    =goal>
        decision-state execute-strategy
        ;distance-y =y
        distance-x =x
        formation-y =y
        aoi-y =agent-y  ; TODO
        obstacle1-x =obstacle-x
        disturbance-value =disturbance
    ?action-intention>
        state free
    =situated-state>
        agent-x =agent-x
    =imaginal>
        strategy strategy-aOO
    !bind! =goal-x (- =obstacle-x =x)
    !bind! =relative-x (- =goal-x =agent-x)
    !bind! =relative-y (- (- =y =agent-y) 50)
    !bind! =time (mp-time-ms)
==>
    =goal>
        decision-state idle
    +action-intention>
        disturbance =disturbance
        x =relative-x
        y =relative-y
        goal-x =goal-x
        type strategy-aOO
    =situated-state>
    =imaginal>
    !eval! (set-interval-action)
    !eval! (dispatch-apply "logMessage" "model" nil (list "time" (mp-time-ms) "event" "execute strategy" "strategy" "strategy-aOO" "target x" =goal-x "agent x" =agent-x "agent y" =agent-y))
    !eval! (dispatch-apply "getModelState" "execute-strategy-aOO")
)

(p execute-strategy-OOa
    =goal>
        decision-state execute-strategy
        ;distance-y =y
        distance-x =x
        formation-y =y
        aoi-y =agent-y  ; TODO
        disturbance-value =disturbance
    ?action-intention>
        state free
    =situated-state>
        agent-x =agent-x
    =imaginal>
        strategy strategy-OOa
        obstacle2-x =obstacle-x
    !bind! =goal-x (+ =obstacle-x =x)
    !bind! =relative-x (- =goal-x =agent-x)
    !bind! =relative-y (- (- =y =agent-y) 50)
    !bind! =time (mp-time-ms)
==>
    =goal>
        decision-state idle
    +action-intention>
        disturbance =disturbance
        x =relative-x
        y =relative-y
        goal-x =goal-x
        type strategy-OOa
    =situated-state>
    =imaginal>
    !eval! (set-interval-action)
    !eval! (dispatch-apply "logMessage" "model" nil (list "time" (mp-time-ms) "event" "execute strategy" "strategy" "strategy-OOa" "target x" =goal-x "agent x" =agent-x "agent y" =agent-y))
    !eval! (dispatch-apply "getModelState" "execute-strategy-OOa")
)

(p execute-strategy-OaO
    =goal>
        decision-state execute-strategy
        ;distance-y =y
        distance-x =x
        formation-y =y
        aoi-y =agent-y  ; TODO
        obstacle1-x =obstacle-x
        disturbance-value =disturbance
    ?action-intention>
        state free
    =situated-state>
        agent-x =agent-x
    =imaginal>
        strategy strategy-OaO
        
    !bind! =relative-y (- (- =y =agent-y) 50)
    !bind! =goal-x (+ =obstacle-x =x)
    !bind! =relative-x (- =goal-x =agent-x)
    !bind! =time (mp-time-ms)
==>
    =goal>
        decision-state idle
    +action-intention>
        disturbance =disturbance
        x =relative-x
        y =relative-y
        goal-x =goal-x
        type strategy-OaO
    =situated-state>
    =imaginal>
    !eval! (set-interval-action)
    !eval! (dispatch-apply "logMessage" "model" nil (list "time" (mp-time-ms) "event" "execute strategy" "strategy" "strategy-OaO" "target x" =goal-x "agent x" =agent-x "agent y" =agent-y))
    !eval! (dispatch-apply "getModelState" "execute-strategy-OaO")
)

(p execute-strategy-stay
    =goal>
        decision-state execute-strategy
        ;distance-y =y
        distance-x =x
        formation-y =y
        aoi-y =agent-y  ; TODO
        disturbance-value =disturbance
    ?action-intention>
        state free
    =situated-state>
        agent-x =agent-x
    =imaginal>
        strategy strategy-stay
        
    !bind! =relative-y (- (- =y =agent-y) 50)
    !bind! =goal-x (+ =agent-x 0)
    !bind! =relative-x (- =goal-x =agent-x)
    !bind! =time (mp-time-ms)
==>
    =goal>
        decision-state idle
    +action-intention>
        disturbance =disturbance
        x =relative-x
        y =relative-y
        goal-x =goal-x
        type strategy-stay
    =situated-state>
    =imaginal>
    !eval! (set-interval-action)
    !eval! (dispatch-apply "logMessage" "model" nil (list "time" (mp-time-ms) "event" "execute strategy" "strategy" "strategy-stay" "target x" =goal-x "agent x" =agent-x "agent y" =agent-y))
    !eval! (dispatch-apply "getModelState" "execute-strategy-stay")
)


(p monitor-soc-too-low
    =goal>
        decision-state idle
        soc-threshold =threshold
        soc-time-window =window
    =situated-state>
        high-level-soc =soc
    !eval! (< =soc =threshold)
    !eval! (interval-test-action =window)
==>
    =goal>
        decision-state ineffective-strategy ; trigger ineffective-strategy
    !eval! (dispatch-apply "getModelState" "monitor-soc-too-low")
)
(spp monitor-soc-too-low :u 10)

(p ineffective-strategy
    =imaginal>
    =action-intention>
        type =action
    =goal>
        decision-state ineffective-strategy
==>
    =action-intention>
    =imaginal>
        result "ineffective"
    =goal>
        decision-state select-strategy
        explain-state explain-soc
    !eval! (dispatch-apply "logMessage" "model" nil (list "time" (mp-time-ms) "event" "ineffective strategy" "strategy" =action))
    !eval! (dispatch-apply "getModelState" "ineffective-strategy")
)


(p monitor-situation    ; this production immediately interrupts any ongoing decision making processes, as they are now invalid
    =goal>
        formation =formation
    =situated-state>
        - situation no-change
    ;!eval! (not (eql =last-situation =situation))
    =imaginal>
        disturbance =disturbance
        formation =old-formation
        strategy =old-strategy
        result =old-result
        position =old-position
    ?imaginal>
        state free
==>
    =goal>
        decision-state build-action-field
    =situated-state>
        situation no-change ; overwrite
    +imaginal>
        formation =formation
        disturbance =disturbance
    !eval! (dispatch-apply "logMessage" "model" nil (list "time" (mp-time-ms) "event" "situation changed" "formation" =formation "disturbnce" =disturbance))
    !eval! (dispatch-apply "getModelState" "monitor-situation")
    !eval! (dispatch-apply "logMessage" "model" nil (list "time" (mp-time-ms) "event" "new imaginal" "formation" =old-formation "disturbnce" =disturbance "strategy" =old-strategy "result" =old-result "position" =old-position))
    
)
(spp monitor-situation :u 7)

; crash detection
; TODO implement crash handling, reduce reliability ( or use chunk activation?)
;
(p crash-occurred
    =imaginal>
    =situated-state>
        crash "True"
    ==>
    =situated-state>
        crash "False"
        situation crash-change
    =imaginal>
        result "crash"
    !eval! (dispatch-apply "logMessage" "model" nil (list "time" (mp-time-ms) "event" "crash"))
    !eval! (dispatch-apply "getModelState" "crash-occurred")
)

(spp crash-occurred :u 10)

(p monitor-formation-idle    ; this production immediately interrupts any ongoing decision making processes, as they are now invalid
    ; situation has changed (obstacle formation passed or cone passed)
    =goal>
        vision-state idle
        formation =formation
    =situated-state>
        - situation formation-change
    =imaginal>
        formation =current-formation
        strategy =strategy
        - strategy nil
    !eval! (not (eql =current-formation =formation))
==>
    =goal>
    =situated-state>
        situation formation-change
    =imaginal>
        result "success"
    !eval! (dispatch-apply "logMessage" "model" nil (list "time" (mp-time-ms) "event" "situation passed" "learned" =strategy))
    !eval! (dispatch-apply "getModelState" "monitor-formation-idle")
)
(spp monitor-formation-idle :u 7)

(p monitor-formation-idle-no-strategy    ; this production immediately interrupts any ongoing decision making processes, as they are now invalid
    ; situation has changed (obstacle formation passed or cone passed)
    =goal>
        vision-state idle
        formation =formation
    =situated-state>
        - situation formation-change
    =imaginal>
        formation =current-formation
        strategy nil
    !eval! (not (eql =current-formation =formation))
==>
    =goal>
    =situated-state>
        situation formation-change
    =imaginal>
        result "success"
    !eval! (dispatch-apply "logMessage" "model" nil (list "time" (mp-time-ms) "event" "situation passed"))
    !eval! (dispatch-apply "getModelState" "monitor-formation-idle-no-strategy")
)
(spp monitor-formation-idle-no-strategy :u 7)

(p monitor-formation-track-formation    ; this production immediately interrupts any ongoing decision making processes, as they are now invalid
    ; situation has changed (obstacle formation passed or cone passed)
    =goal>
        vision-state track-formation
        formation =formation
    =situated-state>
        - situation formation-change
    =imaginal>
        formation =current-formation
    !eval! (not (eql =current-formation =formation))
==>
    =goal>
    =situated-state>
        situation formation-change
    =imaginal>
        result "success"
    !eval! (dispatch-apply "logMessage" "model" nil (list "time" (mp-time-ms) "event" "situation passed"))
    !eval! (dispatch-apply "getModelState" "monitor-formation-track-formation")
)
(spp monitor-formation-track-formation :u 7)

(p monitor-formation-track-cone    ; this production immediately interrupts any ongoing decision making processes, as they are now invalid
    ; situation has changed (obstacle formation passed or cone passed)
    =goal>
        vision-state track-cone
        formation =formation
    =situated-state>
        - situation formation-change
    =imaginal>
        formation =current-formation
        strategy =strategy
    !eval! (not (eql =current-formation =formation))
==>
    =goal>
    =situated-state>
        situation formation-change
    =imaginal>
        result "success"
    !eval! (dispatch-apply "logMessage" "model" nil (list "time" (mp-time-ms) "event" "situation passed" "learned" =strategy))
    !eval! (dispatch-apply "getModelState" "monitor-formation-track-cone")
)
(spp monitor-formation-track-cone :u 7)

(p monitor-formation-track-cone-no-strategy    ; this production immediately interrupts any ongoing decision making processes, as they are now invalid
    ; situation has changed (obstacle formation passed or cone passed)
    =goal>
        vision-state track-cone
        formation =formation
    =situated-state>
        - situation formation-change
    =imaginal>
        formation =current-formation
        strategy nil
    !eval! (not (eql =current-formation =formation))
==>
    =goal>
    =situated-state>
        situation formation-change
    =imaginal>
        result "success"
    !eval! (dispatch-apply "logMessage" "model" nil (list "time" (mp-time-ms) "event" "situation passed"))
    !eval! (dispatch-apply "getModelState" "monitor-formation-track-cone-no-strategy")
)
(spp monitor-formation-track-cone-no-strategy :u 7)

#|
(p monitor-disturbance    ; this production immediately interrupts any ongoing decision making processes, as they are now invalid
    =goal>
        disturbance =disturbance
    =situated-state>
    =imaginal>
        disturbance =current-disturbance
    !eval! (not (eql =current-disturbance =disturbance))
==>
    =goal>
        disturbance =current-disturbance
    =situated-state>
        situation disturbance-change
    =imaginal>
)
(spp monitor-disturbance :u 7)

|#

; vision loop  updates situation field
; obstacle positions: left 600, center 700, right 800

(p look-for-obstacle    ;; initiate obstacle search, reset values etc.
    =goal>
        vision-state   idle
        aoi-y =y  ; area of interest starts at the center of the screen
    !eval! (interval-test 150)
    =imaginal>
    - formation situation-cone ; do not look for obstacles when inside a cone... this makes the model run, but its not a good model
 ==>
    =goal>
        vision-state   find-obstacle
        obstacle-x 0
        boundary-y-1 =y 
        boundary-y-2 1000 ; screen height, todo fix hardcoded value
        obstacle1-x nil
        obstacle2-x nil
        formation nil
    =imaginal>

    !eval! (set-interval-obstacle)
)

(spp look-for-obstacle :u 3)

(p find-obstacle    ;; find obstacle
    =goal>
        vision-state   find-obstacle
        obstacle-x =x
        boundary-y-1 =y1
        boundary-y-2 =y2
 ==>
    +visual-location>
        kind oval
        color black
        > screen-x =x ;; look for leftmost item based on previous search (can be 0)
        >= screen-y =y1  ; look for item below spaceship (higher y)
        < screen-y =y2  ; this prevents search to find obstacles 
        screen-y lowest ; from farther away formations
        screen-x lowest
    =goal>
        vision-state   encode-obstacle
)

(p encode-obstacle-but-wrong-item-found-retry
    =goal>
        vision-state   encode-obstacle
    =visual-location>
        - kind oval
==>
    =goal>
        vision-state find-obstacle
    -visual-location>
;    =goal>
;        vision-state   find-obstacle
;        obstacle-x 0
;        boundary-y-1 =y
;        boundary-y-2 1000 ; screen height, todo fix hardcoded value
;    =imaginal>
;        obstacle1-x nil
;        obstacle2-x nil
;        formation nil
)

(p encode-obstacle-failure-no-obstacles-found-at-all
    =goal>
        vision-state   encode-obstacle
        formation nil
    ?visual-location>
        state   error
==>
    =goal>
        vision-state       idle
        obstacle-x nil
        obstacle1-x nil
        obstacle2-x nil
        formation situation----
)

(p encode-obstacle-failure-obstacles-previously-found
    =goal>
        vision-state   encode-obstacle
        - formation nil
    ?visual-location>
        state   error
==>
    =goal>
        vision-state       track-formation
)

(p encode-obstacle-left
; is always the first obstacle to be encoded if it is present
    =goal>
        vision-state   encode-obstacle
    =visual-location>
        kind oval
        color black
        screen-x =x
        screen-y =y
    !eval! (< =x 650)
==>
    =goal>
        vision-state   find-obstacle
        boundary-y-2 =y
        obstacle-x =x
        formation-y =y
        obstacle1-x =x
        obstacle2-x nil
        formation situation-o--

)

(p encode-obstacle-center
    =goal>
        vision-state   encode-obstacle
        obstacle1-x nil
        formation nil
    =visual-location>
        kind oval
        color black
        screen-x =x
        screen-y =y
    !eval! (and (< =x 750) (> =x 650))
==>
    =goal>
        vision-state   find-obstacle
        boundary-y-2 =y
        obstacle-x =x
        formation-y =y
        obstacle1-x =x
        obstacle2-x nil
        formation situation--o-
)

(p encode-obstacle-center-formation-left
; only two obstacles possible, abort search
    =goal>
        vision-state   encode-obstacle
        formation situation-o--
        - obstacle1-x nil
    =visual-location>
        kind oval
        color black
        screen-x =x
        screen-y =y
    !eval! (and (< =x 750) (> =x 650))
==>
    =goal>
        vision-state   track-formation
        boundary-y-2 =y
        obstacle-x =x
        formation-y =y
        obstacle2-x =x
        formation situation-oo-
)


(p encode-obstacle-right
; no formation found, but also no more obstacles possible, abort search
    =goal>
        vision-state   encode-obstacle
        formation nil
    =visual-location>
        kind oval
        color black
        screen-x =x
        screen-y =y
    !eval! (> =x 750)
==>
    =goal>
        vision-state   track-formation
        boundary-y-2 =y
        obstacle-x =x
        formation-y =y
        obstacle1-x =x
        obstacle2-x nil
        formation situation---o
)

(p encode-obstacle-right-formation-left
; no more obstacles possible, abort search
    =goal>
        vision-state   encode-obstacle
        formation situation-o--
        - obstacle1-x nil
    =visual-location>
        kind oval
        color black
        screen-x =x
        screen-y =y
    !eval! (> =x 750)
==>
    =goal>
        vision-state   track-formation
        boundary-y-2 =y
        obstacle-x =x
        formation-y =y
        obstacle2-x =x
        formation situation-o-o
)

(p encode-obstacle-right-formation-center
; no more obstacles possible, abort search
    =goal>
        vision-state   encode-obstacle
        formation situation--o-
        - obstacle1-x nil
    =visual-location>
        kind oval
        color black
        screen-x =x
        screen-y =y
    !eval! (> =x 750)
==>
    =goal>
        vision-state track-formation
        boundary-y-2 =y
        obstacle-x =x
        formation-y =y
        obstacle2-x =x
        formation situation--oo
)

(p track-formation
    =goal>
        vision-state   track-formation
        boundary-y-1 =y1
        boundary-y-2 =y2
        obstacle-x =x
        !eval! (interval-test 100)
==>
    +visual-location>
        kind oval
        color black
        = screen-x =x ;; look for same object
        >= screen-y 500  ; TODO hard coded value =y1 object moves up
        <= screen-y =y2  ;
    =goal>
        vision-state   track-obstacle-encode
    !eval! (set-interval-obstacle)
)



(p attend-tracked-object
    =goal>
        vision-state   track-obstacle-encode
    =visual-location>
        kind oval
        color black
        screen-x =x
        screen-y =y
==>
    =goal>
      vision-state       track-formation
      boundary-y-2 =y ; update boundary
      formation-y =y
)

(p attend-tracked-object-failure
; obstacle formation passed
    =goal>
        vision-state   track-obstacle-encode
    ?visual-location>
        state   error
==>
    =goal>
        vision-state       idle
        formation situation----       
)


;; find-border, find-obstacle, find-driftmarker


;; find borders to detect if next situation is a cone
(p find-cone
    =goal>
        cone-x nil
        vision-state   idle
        ;aoi-y  =y
    !eval! (interval-test-border 150)
 ==>
    +visual-location>
        kind line
        color blue
        >= screen-y 950  ; look for item ahead, including offsets of line renderings...
    =goal>
        vision-state   encode-border
    !eval! (set-interval-border)
)

(spp find-cone :u 1)


(p encode-border-failure
    =goal>
        vision-state   encode-border
    ?visual-location>
        state   error
==>
    =goal>
        vision-state       idle
        cone-x nil
        formation situation----
)

(p encode-border-is-cone
    =goal>
        vision-state   encode-border
    =visual-location>
        color blue
        screen-x =x
==>
    =goal>
        vision-state   idle
        cone-x =x
        formation situation-cone      
)

(p track-cone
    =goal>
        vision-state   idle
        cone-x =x
        ;aoi-y  =y
    !eval! (interval-test-border 100)
==>
    +visual-location>
        kind line
        color blue
        = screen-x =x ;; look for same object
        < screen-y 950
        > screen-y 130
    =goal>
        vision-state   track-cone-encode
    !eval! (set-interval-border)
)


(p attend-tracked-cone-failure
; obstacle formation passed
    =goal>
        vision-state   track-cone-encode
    ?visual-location>
        state   error
==>
    =goal>
        vision-state       idle
        cone-x nil
        formation situation----
)


(p encode-tracked-cone
    =goal>
        vision-state   track-cone-encode
    =visual-location>
        color blue
==>
    =goal>
        vision-state   idle
        formation situation-cone       
)




;;; find driftmarkers


(p find-driftmarker    ;;
    =goal>
        vision-state   idle
    !eval! (interval-test-drift 150)
 ==>
    +visual-location>
        ; > screen-y 550
        kind oval
        - color black
        - color green
    =goal>
        vision-state   encode-driftmarker
    !eval! (set-interval-drift)
)

(spp find-driftmarker :u 2)

(p encode-driftmarker-not-reached
    =goal>
        vision-state   encode-driftmarker
    =visual-location>
            color =color
        > screen-y 950    ; has not reached agents position yet
    =imaginal>
    !bind! =disturbance (color-to-disturbance =color)
==>
    =goal>
        vision-state       idle
    =imaginal>
        disturbance "disturbance-dont-care"
)

(p encode-driftmarker-reached
    =goal>
        vision-state   encode-driftmarker
    =visual-location>
            color =color
       < screen-y 949    ; position of agent y
       > screen-y 130
    =imaginal>
    !bind! =disturbance (color-to-disturbance =color)
==>
    =goal>
        vision-state       idle
    =imaginal>
        disturbance =disturbance      
)
(spp encode-driftmarker-reached :u 10)

(p encode-driftmarker-passed
    =goal>
        vision-state   encode-driftmarker
    =visual-location>
       < screen-y 130
    =imaginal>
==>
    =goal>
        vision-state       idle
    =imaginal>
        disturbance "disturbance-dont-care"    
)

(spp encode-driftmarker-passed :u 1)

(p encode-driftmarker-failure
    =goal>
        vision-state   encode-driftmarker
    ?visual-location>
        state error
    =imaginal>
==>
    =goal>
        vision-state       idle
    =imaginal>
        disturbance "disturbance-dont-care"  
)



(P reset-model
    =goal>
        state reset
    =situated-state>
    ?action-intention>
        state free
    ?imaginal>
        state free
    !bind! =dont-care (update-timers)
    !bind! =time (mp-time-ms)
 ==>
    =goal>
        state do-not-reset
        decision-state build-action-field
        vision-state idle
        distance-y 100
        distance-x 50
    =situated-state>
        agent green
        situation no-change
        agent-x 400
        high-level-goal avoid
        high-level-soc 0.57 ; 0.3 0.5 0.7
    +action-intention>
        disturbance -1000
        x 0
        y 200
        goal-x 0
        time =time
    +imaginal>  ; prepare imaginal chunk
        disturbance "disturbance-dont-care"
        formation situation----
        position "position-center"
        time =time
)
(spp reset-model :u 100)

#|
(p goal-reached
    =goal>
        soc-threshold =threshold
        soc-boost =soc-boost
        disturbance-value =disturbance
    =situated-state>
        agent-x =agent-x
        high-level-soc =soc
    =action-intention>
        goal-x =goal-x
        - type strategy-stay
    ?action-intention>
        state free
    =imaginal>
        
    !eval! (goal-reached =agent-x =goal-x 2)
    !bind! =soc-new (increase-soc =soc (* =soc-boost =threshold))
    !bind! =time (mp-time-ms)
    ==>
    -action-intention>
    =goal>
        decision-state start
    -situated-state>
    -imaginal>
)
|#

;; sense of control evaluation productions, trying to find explanations for low soc

(p low-soc-no-disturbance
    =goal>
        explain-state explain-soc
    =imaginal>
        disturbance "disturbance-dont-care"
    =situated-state>
    ==>
    =situated-state>
        situation disturbance-change
    =imaginal>
        disturbance "disturbance-weak"
    =goal>
        explain-state idle
    !eval! (dispatch-apply "getModelState" "low-soc-no-disturbance")
)

(p low-soc-weak-disturbance
    =goal>
        explain-state explain-soc
    =imaginal>
        disturbance "disturbance-weak"
    =situated-state>
    ==>
    =situated-state>
        situation disturbance-change
    =imaginal>
        disturbance "disturbance-medium"
    =goal>
        explain-state idle
    !eval! (dispatch-apply "getModelState" "low-soc-weak-disturbance")
)

(p low-soc-medium-disturbance
    =goal>
        explain-state explain-soc
    =imaginal>
        disturbance "disturbance-medium"
    =situated-state>
    ==>
    =situated-state>
        situation disturbance-change
    =imaginal>
        disturbance "disturbance-strong"
    =goal>
        explain-state idle
    !eval! (dispatch-apply "getModelState" "low-soc-medium-disturbance")
)

(p low-soc-strong-disturbance
    =goal>
        explain-state explain-soc
    =imaginal>
        disturbance "disturbance-strong"
    =situated-state>
    ==>
    =situated-state>
        situation disturbance-change
    =imaginal>
        disturbance "disturbance-stochastic"
    =goal>
        explain-state idle
    !eval! (dispatch-apply "getModelState" "low-soc-strong-disturbance")
)

(p low-soc-stochastic-disturbance
    =goal>
        explain-state explain-soc
    =imaginal>
        disturbance "disturbance-stochastic"
    =situated-state>
    ==>
    =imaginal>
    =situated-state>
        situation disturbance-change
    =goal>
        explain-state idle
    !eval! (dispatch-apply "getModelState" "low-soc-stochastic-disturbance")
)


)