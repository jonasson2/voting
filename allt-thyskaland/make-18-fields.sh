#!/bin/bash
gawk -F';' 'BEGIN  {OFS=";"}
            NF==17 {$0 = $0 ";"}
            //     {print}' $1
           
