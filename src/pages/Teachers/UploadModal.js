import React, { useState } from 'react';
import { Button, Modal, ModalHeader, ModalBody, ModalFooter, Input, Label, Form, FormGroup } from 'reactstrap';
import ReactStars from "react-rating-stars-component";
import './../style/ModalForFeedback.css';
import axios from 'axios';
import basename from "../Home/basename.js";
import { Alert } from 'reactstrap';
import { Redirect } from 'react-router';
import Snackbar from '@material-ui/core/Snackbar';
import MuiAlert from '@material-ui/lab/Alert';
import { makeStyles } from '@material-ui/core/styles';

function Alert1(props) {
    return <MuiAlert elevation={6} variant="filled" {...props} />;
  }
  
const useStyles = makeStyles((theme) => ({
    root: {
      width: '100%',
      '& > * + *': {
        marginTop: theme.spacing(2),
      },
    },
  }));

const UploadModal = (props) => {
    const className = props.className;
    const buttonLabel = props.buttonLabel;
    const [modal, setModal] = useState(false);
    const toggle = () => {setModal(!modal);}
    const [upload,setUpload] = useState({});
    const course_id = props.match.params['id'];
    const [error,setError] = useState(false);

    const classes = useStyles();
    const [open, setOpen] = React.useState(false);
  
    const handleClick = () => {
      setOpen(true);
    };
  
    const handleClose = (event, reason) => {
      if (reason === 'clickaway') {
        return;
      }
  
      setOpen(false);
    };


    const changeField = (e) =>{
        const field = e.target.name;
        const value = e.target.value;
        setUpload(prev=>{
            return {...prev,[field]:value};
        })
    }
    
    function validate_formdata(){
        if(upload['topic']==="" || upload['description']===""){
            return false;
        }
        return true;
    }

    const submitData = () =>{
        if(validate_formdata){
            let formdata = new FormData();
            var filedata = document.getElementById("file");
            formdata.append('pdf',filedata.files[0],filedata.files[0].name);
            formdata.append('topic',upload['topic']);
            formdata.append('description',upload['description']);
            if(className==="assignments") {
                formdata.append('deadline',upload['deadline']);
            }
            axios.get(`${basename}/api/course/${course_id}/`)
                .then(res=>{
                    formdata.append('course',res.data['resource_uri']);
                    axios({
                        method: 'post',
                        url: `${basename}/api/${props['content']}/`,
                        data: formdata,
                        header: {
                                'Accept': 'application/json',
                                'Content-Type': 'multipart/form-data',
                                },
                        }).then(()=>{toggle();window.location.reload(false);}
                        )
                });
                handleClick();
        }
        else{
            setError(true);
        }
    }
    const ErrorStatement = ()=>{
        if(error){
            return(
            <p>Please Upload content in {className}</p>
            )
        }
        else return null;
    }
    const Formg = () =>{
        if(className==="assignments"){
            return(
                <FormGroup>
                <Label for="deadline">Deadline</Label>
                    <Input
                    type="date"
                    name="deadline"
                    id="deadline"
                    placeholder="date placeholder"
                    size="lg"
                    value={upload['deadline']}
                    onChange={changeField}
                />
                </FormGroup>
            )    
        }
        else{
            return null;
        }
    }
    const styleModal = {
        height:"300px",
    };
    console.log(upload);
    return (
        <div>
        <Snackbar open={open} autoHideDuration={6000} onClose={handleClose}>
            <Alert1 onClose={handleClose} severity="success" style={{"fontSize":"13px"}}>
                {className} is uploaded successfully!
            </Alert1>
        </Snackbar>
        <div style={{marginTop:"10px"}}>
            <Button color="danger" onClick={toggle} size="lg" style = {props.buttonStyle}>{buttonLabel}</Button>
            <Modal isOpen={modal} toggle={toggle} className={className} >
                <ModalHeader toggle={toggle}>Upload Form</ModalHeader>
                <ModalBody>
                    <ErrorStatement/>
                    <Form style={{marginBottom:"20px",fontSize:"17px"}}>
                        <FormGroup>
                            <Label for="topic">Topic</Label>
                            <Input type="text" name="topic" id="topic" placeholder="Enter a topic" size="lg" onChange={changeField}/>
                        </FormGroup>
                        <FormGroup>
                            <Label for="desc">Brief description</Label>
                            <Input type="textarea" name="description" id="desc" size="lg" onChange={changeField}/>
                        </FormGroup>
                        <FormGroup>
                            <Label for="file">File</Label>
                            <Input type="file" name="pdf" id="file" />
                        </FormGroup>
                        <Formg />
                    </Form>   
                </ModalBody>
                <ModalFooter >
                    <Button color="primary" size="lg" onClick={submitData}>Upload</Button>{' '}
                    <Button color="secondary" onClick={toggle} size="lg">Cancel</Button>
                </ModalFooter>
            </Modal>
        </div>
        </div>
    );
}

export default UploadModal;