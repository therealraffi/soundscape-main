package com.example.soundy;

import androidx.annotation.NonNull;
import androidx.annotation.RequiresApi;
import androidx.appcompat.app.AppCompatActivity;

import android.animation.Animator;
import android.animation.AnimatorListenerAdapter;
import android.animation.ObjectAnimator;
import android.animation.PropertyValuesHolder;
import android.content.res.Resources;
import android.graphics.Color;
import android.graphics.Path;
import android.os.Build;
import android.os.Bundle;
import android.os.SystemClock;
import android.view.View;
import android.view.ViewAnimationUtils;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;

import com.google.firebase.database.DataSnapshot;
import com.google.firebase.database.DatabaseError;
import com.google.firebase.database.DatabaseReference;
import com.google.firebase.database.FirebaseDatabase;
import com.google.firebase.database.ValueEventListener;

public class MainActivity extends AppCompatActivity {
    ImageView[] image;
    ImageView[] orbs;
    TextView[] text;
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        image = new ImageView[4];

        image[0]=(ImageView) findViewById(R.id.locate0);
        image[1]=(ImageView) findViewById(R.id.locate1);
        image[2]=(ImageView) findViewById(R.id.locate2);
        image[3]=(ImageView) findViewById(R.id.locate3);


        for (int i=0;i<4;i++)
        {
            image[i].getLayoutParams().height = (int) (.05*getScreenWidth());
            image[i].getLayoutParams().width = (int) (.05*getScreenWidth());
            image[i].setVisibility(View.GONE);
        }

        orbs = new ImageView[4];
        orbs[0] = (ImageView) findViewById(R.id.orb1);
        orbs[1]=(ImageView) findViewById(R.id.orb2);
        orbs[2]=(ImageView) findViewById(R.id.orb3);
        orbs[3]=(ImageView) findViewById(R.id.orb4);


        text = new TextView[4];
        text[0] = (TextView) findViewById(R.id.text1);
        text[1] = (TextView) findViewById(R.id.text2);
        text[2] = (TextView) findViewById(R.id.text3);
        text[3] = (TextView) findViewById(R.id.text4);

        for(int i=0;i<4;i++)
        {
            orbs[i].getLayoutParams().height = (int) (.08*getScreenWidth());
            orbs[i].getLayoutParams().width = (int) (.08*getScreenWidth());
            orbs[i].setY((float) (getScreenHeight()*(.42+i*.1)));
            orbs[i].setX((float) (getScreenWidth()*.05));
            text[i].setY((float) (getScreenHeight()*(.4285+i*.1)));
            text[i].setX((float) (getScreenWidth()*.20));
            text[i].getLayoutParams().height = (int) (.08*getScreenWidth());
            text[i].getLayoutParams().width = (int) (.8 *getScreenWidth());
        }



        final ImageView circle = findViewById(R.id.circle);
        circle.requestLayout();
        circle.getLayoutParams().height = (int) (getScreenWidth()*.50);
        circle.getLayoutParams().width = (int) (getScreenWidth()*.50);

        final int circleRadius = (int) ((getScreenWidth()*.50)/2.0);

        circle.setX((float) (getScreenWidth()/2.0 - (getScreenWidth()*.50)/2.0));
        circle.setY((float) (getScreenHeight()*.1));

        final ImageView filled = findViewById(R.id.filled);

        int filledRadius = (int) (getScreenWidth()*.20);

        filled.getLayoutParams().height = filledRadius;
        filled.getLayoutParams().width = filledRadius;

        float filledX= (float) (getScreenWidth()/2.0 - (filledRadius/2.0));
        float filledY= (float) ((getScreenHeight()*.1+((getScreenWidth()*.50)/2.0)) -(filledRadius)/2.0);
        filled.setX(filledX);
        filled.setY(filledY);

        ObjectAnimator scaleDown = ObjectAnimator.ofPropertyValuesHolder(
                filled,
                PropertyValuesHolder.ofFloat("scaleX", 1.2f),
                PropertyValuesHolder.ofFloat("scaleY", 1.2f));
        scaleDown.setDuration(1500);

        scaleDown.setRepeatCount(ObjectAnimator.INFINITE);
        scaleDown.setRepeatMode(ObjectAnimator.REVERSE);

        scaleDown.start();

        final float centerX= (float) (filled.getX()+filledRadius/2.0);
        final float centerY = (float) (filledY+filledRadius/2.0);

        Toast.makeText(MainActivity.this,"X axis for filled "+
                filled.getX() +"and Y axis is "+filled.getY(),Toast.LENGTH_LONG).show();
        Toast.makeText(MainActivity.this,"X axis is "+circle.getX() +"and Y axis is "+circle.getY(),Toast.LENGTH_LONG).show();
        final FirebaseDatabase database = FirebaseDatabase.getInstance();


        final DatabaseReference sound = database.getReference("Sound");
        sound.addValueEventListener(new ValueEventListener() {
            @Override
            public void onDataChange(@NonNull DataSnapshot dataSnapshot) {
                int count=0;
                for (DataSnapshot snapshot: dataSnapshot.getChildren())
                {
                    String speaking = snapshot.child("speaking").getValue().toString();
                    String content = snapshot.child("content").getValue().toString();

                    if (speaking.equals("true"))
                    {
                        text[count].setText(content);
                    }

                    count++;
                }
            }

            @Override
            public void onCancelled(@NonNull DatabaseError error) {

            }
        });

        DatabaseReference xyval = database.getReference("x_and_y");
        xyval.addValueEventListener(new ValueEventListener() {
            @RequiresApi(api = Build.VERSION_CODES.LOLLIPOP)
            @Override
            public void onDataChange(@NonNull DataSnapshot dataSnapshot) {
                int count=0;
                for (DataSnapshot snapshot : dataSnapshot.getChildren()) {
                    String color = snapshot.child("color").getValue().toString();
                    orbs[count].setColorFilter(Color.parseColor(color));
                    String[] val = snapshot.child("cords").getValue().toString().split(" ");
                    image[count].setColorFilter(Color.parseColor(color));
                    float constant = (float) ((.06*getScreenWidth())/2.0);
                    if (Float.parseFloat(val[0])<0 || Float.parseFloat(val[1])<0)
                        constant = (float) ((.03*getScreenWidth())/2.0);
                    float audioX = centerX + Float.parseFloat(val[0]) * circleRadius ;
                    float audioY = centerY + Float.parseFloat(val[1]) * circleRadius ;
                    image[count].setX((float) (audioX-constant));
                    image[count].setY((float)(audioY-constant));
                    String b = snapshot.child("visibility").getValue().toString();
                    if (b.equals( "true"))
                    {
                        if (snapshot.child("speaking").getValue().toString().equals("false")) {
                            text[count].setText(snapshot.child("classification").getValue().toString());
                        }
                        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
                            // get the center for the clipping circle
                            int cx = image[count].getWidth() / 2;
                            int cy = image[count].getHeight() / 2;

                            // get the final radius for the clipping circle
                            float finalRadius = (float) Math.hypot(cx, cy);

                            // create the animator for this view (the start radius is zero)
                            Animator anim = ViewAnimationUtils.createCircularReveal(image[count], cx, cy, 0f, finalRadius);

                            // make the view visible and start the animation
                            image[count].setVisibility(View.VISIBLE);
                            anim.start();
                        } else {
                            // set the view to invisible without a circular reveal animation below Lollipop
                            image[count].setVisibility(View.INVISIBLE);
                        }
                    }
                    else if (b.equals("false"))
                    {
                        text[count].setText("No Sound Detected");
                        image[count].setVisibility(View.GONE);
                    }
                    count++;
                }
                count=0;
            }

            @Override
            public void onCancelled(@NonNull DatabaseError error) {

            }
        });


    }
    public static int getScreenWidth() {
        return Resources.getSystem().getDisplayMetrics().widthPixels;
    }

    public static int getScreenHeight() {
        return Resources.getSystem().getDisplayMetrics().heightPixels;
    }
}